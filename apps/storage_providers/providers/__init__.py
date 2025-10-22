from .base import BaseStorageProvider
from .discord.discord_provider import DiscordStorageProvider
from .discord_webhook.discord_webhook_provider import DiscordWebhookStorageProvider
# Add more providers as needed

# Platform constants
PLATFORM_DISCORD = "Discord"
PLATFORM_DISCORD_WEBHOOK = "Discord_Webhook"

# List of supported platforms for validation and selection
# The first element is the value stored in DB, the second is the human-readable name 
# (see https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.Field.choices)
PLATFORM_CHOICES = [
    (PLATFORM_DISCORD, "Discord"),
    (PLATFORM_DISCORD_WEBHOOK, "Discord Webhook"),
]

# Centralized provider registry
PROVIDER_REGISTRY = {
    PLATFORM_DISCORD: DiscordStorageProvider,
    PLATFORM_DISCORD_WEBHOOK: DiscordWebhookStorageProvider,
    # Add more providers as needed
}

__all__ = [
    'PROVIDER_REGISTRY',
    'PLATFORM_DISCORD',
    'PLATFORM_CHOICES',
    'BaseStorageProvider',
    'DiscordStorageProvider',
    'DiscordWebhookStorageProvider',
]