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

    def prepare_storage(self, file_metadata:dict) -> dict:
        """
        Prepares storage for a new file (e.g., creates a folder, thread, or container).
        Can also be used to validate configuration before uploads.
        
        This method is optional. Default implementation returns empty dict.
        Override this method if your provider needs to create a storage container
        before uploading chunks (e.g., Discord threads, Telegram topics, S3 buckets).
        
        Args:
            file_metadata: Dict containing basic file info like {"filename": "example.pdf"}
        
        Returns:
            Dict containing provider-specific metadata to store with the File object
            called "storage_context" (e.g., {"thread_id": "123"} for Discord)
        """
        return {}

    @abstractmethod
    def upload_chunk(self, encrypted_chunk:bytes, storage_context:dict) -> dict:
        """
        Uploads a chunk of data and returns the chunk reference,
        alongside storage context (e.g., thread/folder IDs).

        Args:
            encrypted_chunk: The bytes of the chunk to upload, supposedly encrypted.
            storage_context: Dict containing any necessary context for storage
                             (e.g., general upload url) obtained from prepare_storage.
        Returns:
            Dict containing provider-specific chunk reference info that can be used to
            download the chunk later (e.g., {"message_url": "..."})
        """
        pass

    @abstractmethod
    def download_chunk(self, chunk_ref:dict, storage_context:dict) -> bytes:
        """
        Downloads a chunk of data given its chunk reference,
        and any necessary storage context.

        Args:
            chunk_ref: Dict containing chunk reference info (e.g., {"message_url": "..."})
            storage_context: (optional depending on implementation) Dict containing any
                             storage-wide context (e.g., general upload url) obtained
                             from prepare_storage.
        Returns:
            The downloaded bytes of the chunk, supposedly encrypted.
        """
        pass