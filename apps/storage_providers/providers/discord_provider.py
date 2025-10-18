import asyncio
import aiohttp
import logging

from .base import BaseStorageProvider

logger = logging.getLogger(__name__)

class DiscordStorageProvider(BaseStorageProvider):
    """
    The implementation of the storage provider for Discord.
    """

    def __init__(self, config):
        super().__init__(config)
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
        """
        # Get or create a new event loop for this call
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._create_thread_async(file_metadata))

    async def _create_thread_async(self, file_metadata: dict) -> dict:
        """
        Creates a thread in the configured channel using Discord's HTTP API.

        file_metadata is expected to contain at least {"filename": "example.pdf"}
        Returns a dict with at least {"thread_id": "123456789"}
        """
        try:
            filename = file_metadata.get('filename')
            if not filename:
                logger.warning("No filename provided in file_metadata for thread creation. Using 'Untitled'.")
                filename = 'Untitled'
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
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 201:
                        data = await response.json()
                        thread_id = data['id']
                        logger.info(f"Thread created successfully with ID: {thread_id}")
                        return {"thread_id": thread_id}
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create thread. Status: {response.status}, Error: {error_text}")
                        return None
        
        except Exception as e:
            logger.exception(f"An error occurred while creating the Discord thread: {e}")
            return None

    def upload_chunk(self, encrypted_chunk: bytes, file_metadata: dict) -> dict:
        """
        Implements the logic to upload a file chunk to a Discord thread.
        - Gets the thread ID from the file_metadata.
        - Uploads the chunk to the thread.
        - Returns a dictionary containing the provider chunk id, message 
          ID, and maybe message URL, message attachment ID, etc that would
          be useful for downloading later.

        file_metadata is expected to contain at least {"thread_id": "123456789"}
        """
        # Get or create a new event loop for this call
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        thread_id = file_metadata.get("thread_id")
        if not thread_id:
            raise ValueError("file_metadata must contain 'thread_id' for Discord uploads")

        return loop.run_until_complete(self._upload_chunk_async(encrypted_chunk, thread_id))

    async def _upload_chunk_async(self, encrypted_chunk: bytes, thread_id: str) -> dict:
        """
        Uploads a chunk to the specified Discord thread using the Discord API.

        Args:
            encrypted_chunk: The bytes of the encrypted file chunk
            file_metadata: Dictionary containing at least {"thread_id": "123456789"}
        
        Returns:
            Dictionary with upload data response or None on failure. It contains at least:
            {"message_id": "123456789012345678","thread_id": "123456789"}
        """
        if not thread_id:
            raise ValueError("No thread_id provided in file_metadata")
        
        logger.info(f"Starting upload to thread: {thread_id}")
        logger.debug(f"Chunk size: {len(encrypted_chunk)} bytes")
        
        try:
            headers = {
                "Authorization": f"Bot {self.bot_token}"
            }
            
            url = f"{self.api_base}/channels/{thread_id}/messages"
    
            form = aiohttp.FormData()
            form.add_field(
                'files[0]',
                encrypted_chunk,
                filename='chunk.enc',
                content_type='application/octet-stream'
            )
            
            payload_json = {}
            form.add_field('payload_json', aiohttp.JsonPayload(payload_json))
            
            async with aiohttp.ClientSession() as session:
                logger.debug("Sending POST request to Discord API...")
                async with session.post(url, data=form, headers=headers) as response:
                    response_status = response.status
                    response_text = await response.text()
                    if response_status == 200:
                        data = await response.json()

                        # Rename 'id' to 'message_id' for clarity
                        if "id" in data:
                            data["message_id"] = data.pop("id")
                        # Include thread_id for reference (this could be optional)
                        data["thread_id"] = thread_id

                        return data
                    else:
                        logger.error(f"Upload failed with status {response_status}")
                        return None
        
        except Exception as e:
            logger.exception(f"Exception occurred during upload: {type(e).__name__}: {e}")
            return None

    def download_chunk(self, provider_chunk_id, file_metadata):
        """
        Implements the logic to download a file chunk from a Discord thread.
        - Gets message URL or another way of downloading from the 
          file_metadata.
        - Downloads the attachment from the message.
        """
        pass