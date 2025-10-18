import httpx
import logging

from ..base import BaseStorageProvider
from .discord_validator import DiscordConfigValidator
from apps.files.exceptions import StorageUploadError

logger = logging.getLogger(__name__)

class DiscordStorageProvider(BaseStorageProvider):
    """
    The implementation of the storage provider for Discord.
    """

    def __init__(self, config, skip_validation=False, validator=None):
        super().__init__(config)
        
        # Validate the config, because the bot token might expire.
        if not skip_validation:
            if not validator:
                validator = DiscordConfigValidator(config)
            if not validator.validate():
                raise ValueError("Invalid Discord storage provider configuration")
        
        # Initialize the Discord bot client using the provided config
        self.bot_token = self.config.get('bot_token')
        self.server_id = self.config.get('server_id')
        self.channel_id = self.config.get('channel_id')

        self.max_chunk_size = self.config.get('max_chunk_size', 8 * 1024 * 1024)  # Default to 8MB instead of 10MB for overhead

        self.api_base = "https://discord.com/api/v10"


    def prepare_storage(self, file_metadata: dict) -> dict:
        """
        Creates a new Discord thread for the file upload and returns
        the necessary metadata to be stored on the File object.

        file_metadata is expected to contain at least {"filename": "example.pdf"}
        Returns a dict with at least {"thread_id": "123456789"}
        Raises StorageUploadError on failure.
        """
        
        filename = file_metadata.get('filename', 'Untitled')
        thread_name = f"[FILE] {filename}"
        
        logger.info(f"Creating Discord thread: {thread_name}")
        
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        # https://discord.com/developers/docs/resources/channel#start-thread-without-message
        url = f"{self.api_base}/channels/{self.channel_id}/threads"
        payload = {
            "name": thread_name,
            "type": 11,  # PUBLIC_THREAD
            "auto_archive_duration": 10080  # 7 days
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                
                if response.status_code == 201:
                    data = response.json()
                    thread_id = data['id']
                    logger.info(f"Thread created successfully with ID: {thread_id}")
                    return {"thread_id": thread_id}
                else:
                    error_text = response.text
                    logger.error(f"Failed to create thread. Status: {response.status_code}, Error: {error_text}")
                    raise StorageUploadError(f"Discord API error (status {response.status_code}): {error_text}")
        
        except httpx.HTTPError as e:
            logger.exception(f"HTTP error while creating Discord thread: {e}")
            raise StorageUploadError(f"Network error creating thread: {str(e)}") from e
        except Exception as e:
            logger.exception(f"Unexpected error creating Discord thread: {e}")
            raise StorageUploadError(f"Failed to create thread: {str(e)}") from e

    def upload_chunk(self, encrypted_chunk: bytes, file_metadata: dict) -> dict:
        """
        Implements the logic to upload a file chunk to a Discord thread.
        - Gets the thread ID from the file_metadata.
        - Uploads the chunk to the thread.
        - Returns a dictionary containing the provider chunk id, message 
          ID, and maybe message URL, message attachment ID, etc that would
          be useful for downloading later.

        file_metadata is expected to contain at least {"thread_id": "123456789"}
        Raises StorageUploadError on failure.
        """
        
        thread_id = file_metadata.get("thread_id")
        if not thread_id:
            raise ValueError("file_metadata must contain 'thread_id' for Discord uploads")
        
        logger.info(f"Starting upload to thread: {thread_id}")
        logger.debug(f"Chunk size: {len(encrypted_chunk)} bytes")
        
        headers = {
            "Authorization": f"Bot {self.bot_token}"
        }
        
        url = f"{self.api_base}/channels/{thread_id}/messages"
        
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
                response = client.post(url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Rename 'id' to 'message_id' for clarity
                    if "id" in data:
                        data["message_id"] = data.pop("id")
                    # Include thread_id for reference (this could be optional)
                    data["thread_id"] = thread_id

                    logger.info(f"Upload successful. Message ID: {data['message_id']}")
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

    def download_chunk(self, provider_chunk_id, file_metadata):
        """
        Implements the logic to download a file chunk from a Discord thread.
        - Gets message URL or another way of downloading from the 
          file_metadata.
        - Downloads the attachment from the message.
        """
        pass