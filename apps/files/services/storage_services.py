from apps.storage_providers.providers import PROVIDER_REGISTRY
from apps.storage_providers.repository import StorageProviderRepository
from apps.files.exceptions import StorageUploadError, StorageDownloadError

class StorageService:
    """
    A service that abstracts the interaction with different storage providers.
    It delegates the actual upload/download operations to the specific provider's implementation.
    """

    def __init__(self, provider_name, provider_repository=None):
        """
        Initializes the service with a specific provider, given its name.
        """
        if provider_repository is None:
            provider_repository = StorageProviderRepository()

        provider = provider_repository.get_provider_by_name(provider_name)
        if not provider:
            raise ValueError(f"Storage provider '{provider_name}' not found.")

        provider_class = PROVIDER_REGISTRY.get(provider.platform)
        if not provider_class:
            raise ValueError(f"Unsupported storage provider platform: {provider.platform}")
        
        self.provider = provider_class(provider.config)
        self.provider_name = provider_name

    def upload_chunk(self, encrypted_chunk, file_metadata):
        """
        Uploads an encrypted chunk of a file to the configured storage provider.
        - `file_metadata` can contain information like the original filename
          to help the provider decide on "folders" (e.g., Discord thread ID).
        - Returns a dictionary containing provider-specific ID for the stored 
          chunk, and file metadata for future retrieval.
        """
        if not encrypted_chunk:
            raise ValueError("encrypted_chunk cannot be empty")
        if not isinstance(file_metadata, dict):
            raise ValueError("file_metadata must be a dictionary")
        
        try:
            result = self.provider.upload_chunk(encrypted_chunk, file_metadata)

            if not result:
                raise StorageUploadError("Provider returned no result")
            if not isinstance(result, dict):
                raise StorageUploadError(f"Provider returned invalid type: {type(result)}")
            return result
        
        except StorageUploadError:
            raise
        except Exception as e:
            raise StorageUploadError(f"Failed to upload chunk: {str(e)}") from e

    def download_chunk(self, provider_chunk_id, file_metadata):
        """
        Downloads an encrypted chunk from the storage provider.
        """
        if not provider_chunk_id:
            raise ValueError("provider_chunk_id cannot be empty")
        if not isinstance(file_metadata, dict):
            raise ValueError("file_metadata must be a dictionary")
        
        try:
            result = self.provider.download_chunk(provider_chunk_id, file_metadata)
            
            if not result:
                raise StorageDownloadError("Provider returned empty chunk data")
            if not isinstance(result, bytes):
                raise StorageDownloadError(f"Provider returned invalid type: {type(result)}, expected bytes")
            
            return result
            
        except StorageDownloadError:
            raise
        except Exception as e:
            raise StorageDownloadError(f"Failed to download chunk: {str(e)}") from e