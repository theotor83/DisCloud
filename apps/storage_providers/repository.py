from .models import StorageProvider

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