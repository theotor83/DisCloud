import logging
from .models import StorageProvider
from apps.storage_providers.providers import PLATFORM_CHOICES
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseStorageProviderRepository(ABC):
    """
    Abstract base class for storage provider repository implementations.
    Defines the contract for managing StorageProvider objects.
    """

    @abstractmethod
    def get_provider_by_id(self, provider_id):
        """
        Fetch a storage provider by its ID.
        """
        pass

    @abstractmethod
    def get_provider_by_name(self, name):
        """
        Fetch a storage provider by its name.
        """
        pass

    @abstractmethod
    def list_providers(self):
        """
        List all storage providers.
        """
        pass

    @abstractmethod
    def create_provider(self, name, platform, config):
        """
        Create a new storage provider.
        """
        pass

class StorageProviderRepositoryDjango(BaseStorageProviderRepository):
    """
    Django ORM implementation of the BaseStorageProviderRepository.
    Encapsulates all database interactions related to storage providers.
    """

    def __init__(self):
        self.model = StorageProvider

    def get_provider_by_id(self, provider_id):
        """
        Fetch a storage provider by its ID.
        """
        try:
            logger.debug(f"Fetching storage provider by ID: {provider_id}")
            provider = self.model.objects.filter(pk=provider_id).first()
            if provider:
                logger.info(f"Found storage provider: {provider.name} (ID: {provider_id})")
            else:
                logger.warning(f"No storage provider found with ID: {provider_id}")
            return provider
        except Exception as e:
            logger.error(f"Error fetching storage provider by ID {provider_id}: {str(e)}", exc_info=True)
            return None

    def get_provider_by_name(self, name):
        """
        Fetch a storage provider by its name.
        """
        try:
            logger.debug(f"Fetching storage provider by name: {name}")
            provider = self.model.objects.filter(name=name).first()
            if provider:
                logger.info(f"Found storage provider: {provider.name} (Platform: {provider.platform})")
            else:
                logger.warning(f"No storage provider found with name: {name}")
            return provider
        except Exception as e:
            logger.error(f"Error fetching storage provider by name '{name}': {str(e)}", exc_info=True)
            return None

    def list_providers(self):
        """
        List all storage providers.
        """
        try:
            logger.debug("Fetching all storage providers")
            providers = self.model.objects.all()
            logger.info(f"Found {providers.count()} storage provider(s)")
            return providers
        except Exception as e:
            logger.error(f"Error listing storage providers: {str(e)}", exc_info=True)
            return []

    def create_provider(self, name, platform, config):
        """
        Create a new storage provider.
        """
        logger.debug(f"Attempting to create storage provider: {name} (Platform: {platform})")
        
        if not name or not platform or not config or config is None:
            logger.error("Failed to create provider: Name, platform, and config are required")
            raise ValueError("Name, platform, and config are required to create a storage provider.")
        
        if self.model.objects.filter(name=name).exists():
            logger.error(f"Failed to create provider: Provider with name '{name}' already exists")
            raise ValueError(f"Storage provider with name '{name}' already exists.")
        
        if platform not in [choice[0] for choice in PLATFORM_CHOICES]:
            logger.error(f"Failed to create provider: Invalid platform '{platform}'")
            raise ValueError(f"Invalid platform '{platform}'. Must be one of {[choice[0] for choice in PLATFORM_CHOICES]}")
        
        if not isinstance(config, dict):
            logger.error(f"Failed to create provider: Config must be a dictionary, got {type(config).__name__}")
            raise ValueError("Config must be a dictionary.")
        
        provider = self.model.objects.create(
            name=name,
            platform=platform,
            config=config
        )
        logger.info(f"Successfully created storage provider: {provider.name} (ID: {provider.id}, Platform: {provider.platform})")
        return provider