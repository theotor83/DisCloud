import os

from storage_providers.providers.discord_provider import DiscordStorageProvider
from apps.storage_providers.models import StorageProvider
from apps.storage_providers.repository import StorageProviderRepository

class StorageService:
    """
    A service that abstracts the interaction with different storage providers.
    It delegates the actual upload/download operations to the specific provider's implementation.
    """

    def __init__(self, provider_name):
        """
        Initializes the service with a specific provider, given its name.
        """
        provider_repository = StorageProviderRepository()
        provider = provider_repository.get_provider_by_name(provider_name)
        if not provider:
            raise ValueError(f"Storage provider '{provider_name}' not found.")

        if provider.platform == "Discord":
            self.provider = DiscordStorageProvider(provider.config)
        else:
            raise ValueError(f"Unsupported storage provider platform: {provider.platform}")

    def upload_chunk(self, encrypted_chunk, file_metadata):
        """
        Uploads an encrypted chunk of a file to the configured storage provider.
        - `file_metadata` can contain information like the original filename
          to help the provider decide on "folders" (e.g., Discord channels).
        - Returns the provider-specific ID for the stored chunk.
        """
        # Delegate to the provider's `upload_chunk` method.
        pass

    def download_chunk(self, provider_chunk_id):
        """
        Downloads an encrypted chunk from the storage provider.
        """
        # Delegate to the provider's `download_chunk` method.
        pass