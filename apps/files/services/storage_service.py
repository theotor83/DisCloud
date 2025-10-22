from apps.storage_providers.providers import PROVIDER_REGISTRY
from apps.storage_providers.repository import StorageProviderRepositoryDjango
from apps.files.exceptions import StorageUploadError, StorageDownloadError

class StorageService:
    """
    A service that abstracts the interaction with different storage providers.
    It delegates the actual upload/download operations to the specific provider's implementation.
    """

    def __init__(self, provider_name, provider_repository=None, skip_validation=False):
        """
        Initializes the service with a specific provider, given its name.
        
        Args:
            provider_name: Name of the storage provider to use
            provider_repository: Optional repository for fetching provider config
            skip_validation: If True, skip provider configuration validation (useful for testing)
        """
        if provider_repository is None:
            provider_repository = StorageProviderRepositoryDjango()

        provider = provider_repository.get_provider_by_name(provider_name)
        if not provider:
            raise ValueError(f"Storage provider '{provider_name}' not found.")

        provider_class = PROVIDER_REGISTRY.get(provider.platform)
        if not provider_class:
            raise ValueError(f"Unsupported storage provider platform: {provider.platform}")
        
        self.provider = provider_class(provider.config, skip_validation=skip_validation)
        self.provider_name = provider_name

    def prepare_storage(self, file_metadata):
        """
        Prepares storage for a new file upload.
        
        Some providers (like Discord) need to create a storage container (thread)
        before chunks can be uploaded.
        
        Args:
            file_metadata: Dict with file info like {"filename": "example.pdf"}
        
        Returns:
            Dict with provider-specific metadata to store with File object
        """
        if not isinstance(file_metadata, dict):
            raise ValueError("file_metadata must be a dictionary")
        
        try:
            return self.provider.prepare_storage(file_metadata)
        except Exception as e:
            raise StorageUploadError(f"Failed to prepare storage: {str(e)}") from e

    def upload_chunk(self, encrypted_chunk, storage_context):
        """
        Uploads an encrypted chunk of a file to the configured storage provider.
        - `storage_context` can contain information like the original filename
          to help the provider decide on "folders" (e.g., Discord thread ID).
        - Returns a dictionary containing provider-specific ID for the stored 
          chunk, and file metadata for future retrieval.
        """
        if not encrypted_chunk:
            raise ValueError("encrypted_chunk cannot be empty")
        if not isinstance(storage_context, dict):
            raise ValueError("storage_context must be a dictionary")
        
        try:
            result = self.provider.upload_chunk(encrypted_chunk, storage_context)

            if not result:
                raise StorageUploadError("Provider returned no result")
            if not isinstance(result, dict):
                raise StorageUploadError(f"Provider returned invalid type: {type(result)}")
            return result
        
        except StorageUploadError:
            raise
        except Exception as e:
            raise StorageUploadError(f"Failed to upload chunk: {str(e)}") from e

    def download_chunk(self, chunk_ref, storage_context):
        """
        Downloads an encrypted chunk from the storage provider.
        """
        if not chunk_ref:
            raise ValueError("chunk_ref cannot be empty")
        if not isinstance(storage_context, dict):
            raise ValueError("storage_context must be a dictionary")
        
        try:
            result = self.provider.download_chunk(chunk_ref, storage_context)
            
            if not result:
                raise StorageDownloadError("Provider returned empty chunk data")
            if not isinstance(result, bytes):
                raise StorageDownloadError(f"Provider returned invalid type: {type(result)}, expected bytes")
            
            return result
            
        except StorageDownloadError:
            raise
        except Exception as e:
            raise StorageDownloadError(f"Failed to download chunk: {str(e)}") from e
    
    def get_max_chunk_size(self):
        """
        Returns the maximum chunk size supported by the provider.
        This is used by the upload view to determine how to slice the file stream.
        """
        return getattr(self.provider, 'max_chunk_size', 8 * 1024 * 1024)  # Default 8MB