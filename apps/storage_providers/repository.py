from .models import StorageProvider
from apps.storage_providers.providers import PLATFORM_CHOICES

class StorageProviderRepository:
    """
    A repository class to manage storage provider records.
    """

    def __init__(self):
        self.model = StorageProvider

    def get_provider_by_id(self, provider_id):
        """
        Fetch a storage provider by its ID.
        """
        return self.model.objects.filter(pk=provider_id).first()
    
    def get_provider_by_name(self, name):
        """
        Fetch a storage provider by its name.
        """
        return self.model.objects.filter(name=name).first()

    def list_providers(self):
        """
        List all storage providers.
        """
        return self.model.objects.all()
    
    def create_provider(self, name, platform, config):
        """
        Create a new storage provider.
        """
        if not name or not platform or not config or config is None:
            raise ValueError("Name, platform, and config are required to create a storage provider.")
        if self.model.objects.filter(name=name).exists():
            raise ValueError(f"Storage provider with name '{name}' already exists.")
        if platform not in [choice[0] for choice in PLATFORM_CHOICES]:
            raise ValueError(f"Invalid platform '{platform}'. Must be one of {[choice[0] for choice in PLATFORM_CHOICES]}")
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary.")
        
        provider = self.model.objects.create(
            name=name,
            platform=platform,
            config=config
        )
        return provider