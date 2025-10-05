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

    @abstractmethod
    def upload_chunk(self, encrypted_chunk, file_metadata):
        """
        Uploads a chunk of data and returns a provider-specific ID.
        """
        pass

    @abstractmethod
    def download_chunk(self, provider_chunk_id):
        """
        Downloads a chunk of data given its provider-specific ID.
        """
        pass