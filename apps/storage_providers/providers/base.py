from abc import ABC, abstractmethod

class BaseStorageProvider(ABC):
    """
    An abstract base class that all storage providers must implement.
    This defines the contract for how the StorageService will interact with them.
    """

    def __init__(self, config):
        """
        Initializes the provider with its configuration.
        """
        self.config = config

    def prepare_storage(self, file_metadata):
        """
        Prepares storage for a new file (e.g., creates a folder, thread, or container).
        
        This method is optional. Default implementation returns empty dict.
        Override this method if your provider needs to create a storage container
        before uploading chunks (e.g., Discord threads, Telegram topics, S3 buckets).
        
        Args:
            file_metadata: Dict containing file info like {"filename": "example.pdf"}
        
        Returns:
            Dict containing provider-specific metadata to store with the File object
            (e.g., {"thread_id": "123"} for Discord)
        """
        return {}

    @abstractmethod
    def upload_chunk(self, encrypted_chunk, file_metadata):
        """
        Uploads a chunk of data and returns a provider-specific ID,
        alongside file metadata needed for future retrieval.
        """
        pass

    @abstractmethod
    def download_chunk(self, provider_chunk_id, file_metadata):
        """
        Downloads a chunk of data given its provider-specific ID,
        and any necessary file metadata.
        """
        pass