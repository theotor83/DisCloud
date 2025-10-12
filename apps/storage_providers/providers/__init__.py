from .base import BaseStorageProvider
from .discord_provider import DiscordStorageProvider
# Add more providers as needed

# Platform constants
PLATFORM_DISCORD = "Discord"

# List of supported platforms for validation and selection
# The first element is the value stored in DB, the second is the human-readable name 
# (see https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.Field.choices)
PLATFORM_CHOICES = [
    (PLATFORM_DISCORD, "Discord"),
]

# Centralized provider registry
PROVIDER_REGISTRY = {
    PLATFORM_DISCORD: DiscordStorageProvider,
    # Add more providers as needed
}

__all__ = [
    'PROVIDER_REGISTRY',
    'PLATFORM_DISCORD',
    'PLATFORM_CHOICES',
    'BaseStorageProvider',
    'DiscordStorageProvider',
]