from django.db import models

PLATFORM_CHOICES = [
    ('Discord', 'Discord'),
    # Add other platforms as needed
]

class StorageProvider(models.Model):
    """
    Represents a storage service like Discord, Telegram, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    platform = models.CharField(max_length=100, choices=PLATFORM_CHOICES)  # e.g., 'Discord', 'Telegram'...
    # Store any necessary configuration for the provider as a JSON field
    config = models.JSONField()

    def __str__(self):
        return self.name