class StorageService:
    """
    A service that abstracts the interaction with different storage providers.
    It delegates the actual upload/download operations to the specific provider's implementation.
    """

    def __init__(self, provider_name):
        """
        Initializes the service with a specific provider.
        """
        # Dynamically load the provider's class based on provider_name
        pass

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