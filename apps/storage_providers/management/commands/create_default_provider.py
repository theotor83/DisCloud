import os
from django.core.management.base import BaseCommand
from apps.storage_providers.models import StorageProvider
from apps.storage_providers.providers import PLATFORM_DISCORD

class Command(BaseCommand):
    help = 'Creates a default Discord storage provider if it does not exist'

    def handle(self, *args, **options):
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        SERVER_ID = os.getenv('SERVER_ID')
        CHANNEL_ID = os.getenv('CHANNEL_ID')
        if not BOT_TOKEN or not SERVER_ID or not CHANNEL_ID:
            self.stdout.write(self.style.ERROR('BOT_TOKEN, SERVER_ID, and CHANNEL_ID must be set in environment variables.'))
            return

        provider, created = StorageProvider.objects.get_or_create(
            name="discord_default",
            platform=PLATFORM_DISCORD,
            defaults={
                "config": {
                    "bot_token": BOT_TOKEN,
                    "server_id": SERVER_ID,
                    "channel_id": CHANNEL_ID
                }
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created new Discord storage provider.'))
        else:
            self.stdout.write(self.style.WARNING('Discord storage provider already exists.'))