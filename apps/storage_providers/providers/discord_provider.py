import asyncio
import aiohttp

from .base import BaseStorageProvider

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
        self.api_base = "https://discord.com/api/v10"

    def prepare_storage(self, file_metadata):
        """
        Creates a new Discord thread for the file upload and returns
        the necessary metadata to be stored on the File object.
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

    async def _create_thread_async(self, file_metadata):
        """
        Creates a thread in the configured channel using Discord's HTTP API.
        """
        try:
            filename = file_metadata.get('filename', 'Untitled')
            thread_name = f"[FILE] {filename}"
            
            print(f"Creating Discord thread: {thread_name}")
            
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
                        print(f"Thread created successfully with ID: {thread_id}")
                        return {"thread_id": thread_id}
                    else:
                        error_text = await response.text()
                        print(f"Failed to create thread. Status: {response.status}, Error: {error_text}")
                        return None
        
        except Exception as e:
            print(f"An error occurred while creating the Discord thread: {e}")
            return None

    def upload_chunk(self, encrypted_chunk, file_metadata):
        """
        Implements the logic to upload a file chunk to a Discord thread.
        - Creates a new thread in the specified channel.
        - Uploads the chunk to that thread.
        - Returns the thread ID as the provider_chunk_id.
        """
        pass

    def download_chunk(self, provider_chunk_id):
        """
        Implements the logic to download a file chunk from a Discord thread.
        - Fetches the message history of the thread with the given ID.
        - Downloads the attachment from the message.
        """
        pass