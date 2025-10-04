from django.db import models

class StorageProvider(models.Model):
    """
    Represents a storage service like Discord, Telegram, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    # Store any necessary configuration for the provider as a JSON field
    config = models.JSONField()

    def __str__(self):
        return self.name