import httpx
import logging

from ..base import BaseStorageProvider
from .discord_webhook_validator import DiscordWebhookConfigValidator
from apps.files.exceptions import StorageUploadError, StorageDownloadError

logger = logging.getLogger(__name__)

class DiscordWebhookStorageProvider(BaseStorageProvider):
    """
    The implementation of the storage provider for Discord Webhooks.
    """

    def __init__(self, config, skip_validation=False, validator=None):
        super().__init__(config)
        
        # Validate the config, because the bot token might expire.
        if not skip_validation:
            if not validator:
                validator = DiscordWebhookConfigValidator(config)
            #if not validator.validate():
                #raise ValueError("Invalid Discord Webhook storage provider configuration")
        
        # Initialize the Discord bot client using the provided config
        self.webhook_url = self.config.get('webhook_url')

        self.max_chunk_size = self.config.get('max_chunk_size', 8 * 1024 * 1024)  # Default to 8MB instead of 10MB for overhead

        self.api_base = "https://discord.com/api/v10"


    def _get_credentials(self) -> dict:
        """
        Returns a dictionary containing server_id, channel_id, webhook_id, webhook_token
        by making a GET request to its own webhook_url. 

        Meant to be used in prepare_storage.
        """
        logger.debug(f"Fetching credentials for webhook {self.webhook_url}...")
        url = self.webhook_url
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                server_id = data['guild_id']
                channel_id = data['channel_id']
                webhook_id = data['id']
                webhook_token = data['token']
                logger.debug(f"Credentials successfully fetched for webhook {self.webhook_url}: {server_id}, {channel_id}, {webhook_id}, {webhook_token}")
                return {
                    "server_id": server_id,
                    "channel_id": channel_id,
                    "webhook_id": webhook_id,
                    "webhook_token": webhook_token
                }
            else:
                error_text = response.text
                logger.error(f"Failed to fetch credentials. Status: {response.status_code}, Error: {error_text}")
                raise StorageUploadError(f"Discord API error (status {response.status_code}): {error_text}")


    def prepare_storage(self, file_metadata: dict) -> dict:
        """
        Sends a bookmark message using the webhook url. Returns metadata needed
        for uploading chunks later.

        file_metadata should contain {"filename": "example.pdf"} for clarity,
        but it isn't required.
        Returns a dict containing the message_id, the timestamp, the server_id, 
          the channel_id, the webhook_id, the webhook_token, and the message_url.
        Raises StorageUploadError on failure.
        """

        file_metadata_dict = {}
        
        filename = file_metadata.get('filename', 'Unknown')
        message_content = f"Preparing for the upload of {filename}..."
        if len(message_content) > 1950:
            logger.info(f"Message content is too long, truncating to 1950 characters.")
            message_content = message_content[:1950] + "..."
        
        logger.info(f"Creating Discord Webhook bookmark message for file: {filename}")
        
        url = f"{self.webhook_url}?wait=true"
        payload = {
            "content": message_content,
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    file_metadata_dict["timestamp"] = data['timestamp']
                    file_metadata_dict["message_id"] = data['id']
                    file_metadata_dict["channel_id"] = data['channel_id']
                    file_metadata_dict["webhook_id"] = data['webhook_id']
                    logger.info(f"Bookmark message successfully sent with ID: {file_metadata_dict['message_id']}")
                else:
                    error_text = response.text
                    logger.error(f"Failed to send bookmark message. Status: {response.status_code}, Error: {error_text}")
                    raise StorageUploadError(f"Discord API error (status {response.status_code}): {error_text}")
                
            # Get server_id and webhook_token to include in file_metadata_dict
            creds = self._get_credentials()
            file_metadata_dict["server_id"] = creds["server_id"]
            file_metadata_dict["webhook_token"] = creds["webhook_token"]
            file_metadata_dict["message_url"] = f"https://discord.com/channels/{file_metadata_dict['server_id']}/{file_metadata_dict['channel_id']}/{file_metadata_dict['message_id']}"

            return file_metadata_dict
        
        except Exception as e:
            logger.exception(f"Unexpected error creating Discord bookmark message: {e}")
            raise StorageUploadError(f"Failed to create bookmark message: {str(e)}") from e
        except httpx.HTTPError as e:
            logger.exception(f"HTTP error while creating Discord thread: {e}")
            raise StorageUploadError(f"Network error creating thread: {str(e)}") from e

    def upload_chunk(self, encrypted_chunk: bytes, storage_context: dict) -> dict:
        """
        Implements the logic to upload a file chunk using a Discord Webhook.
        - Uses self.webhook_url or storage_context's webhook_url field.
        - Returns a dictionary containing the chunk reference, which
          is the message url that will be used for downloading later. For
          simplicity, it will also include the whole response from Discord API.

        storage_context is a dict that must contain at least webhook_url, server_id, 
        and channel_id.
        Raises StorageUploadError on failure.
        """
        
        webhook_url_metadata = storage_context.get("webhook_url")
        server_id = storage_context.get("server_id")
        channel_id = storage_context.get("channel_id")

        if not webhook_url_metadata:
            logger.warning("storage_context is missing webhook_url. Using self.webhook_url.")
            webhook_url_metadata = self.webhook_url
        if webhook_url_metadata != self.webhook_url:
            logger.warning("Mismatch between storage_context['webhook_url'] and self.webhook_url. Using self.webhook_url.")
            webhook_url_metadata = self.webhook_url

        if not server_id or not channel_id:
            logger.error("storage_context must contain 'server_id' and 'channel_id' for Discord Webhook uploads")
            raise StorageUploadError("storage_context must contain 'server_id' and 'channel_id' for Discord Webhook uploads")
        
        logger.info(f"Starting upload to Discord Webhook: {webhook_url_metadata}")
        logger.debug(f"Chunk size: {len(encrypted_chunk)} bytes")
        
        url = f"{webhook_url_metadata}?wait=true"
        
        files = {
            'files[0]': ('chunk.enc', encrypted_chunk, 'application/octet-stream')
        }
        
        # Discord requires payload_json for message metadata
        data = {
            'payload_json': '{}'  # Empty JSON object
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                logger.debug("Sending POST request to Discord API...")
                response = client.post(url, files=files, data=data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Rename 'id' to 'message_id' for clarity
                    if "id" in data:
                        data["message_id"] = data.pop("id")
                    else:
                        logger.error("Discord API response missing 'id' field")
                        raise StorageUploadError("Discord API response missing 'id' field")
                    # Include message_url for retrieval
                    data["message_url"] = f"https://discord.com/channels/{self.server_id}/{self.channel_id}/{data['message_id']}"
                    # TODO: Should probably validate message_url format here as it is critical

                    logger.info(f"Upload successful. Message URL: {data['message_url']}")
                    return data
                else:
                    error_text = response.text
                    logger.error(f"Upload failed with status {response.status_code}: {error_text}")
                    raise StorageUploadError(
                        f"Discord API error (status {response.status_code}): {error_text}"
                    )
        
        except httpx.HTTPError as e:
            logger.exception(f"HTTP error during chunk upload: {e}")
            raise StorageUploadError(f"Network error uploading chunk: {str(e)}") from e
        except StorageUploadError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during chunk upload: {e}")
            raise StorageUploadError(f"Failed to upload chunk: {str(e)}") from e

    def download_chunk(self, chunk_ref: dict, storage_context: dict) -> bytes:
        """
        TODO
        """
        pass
