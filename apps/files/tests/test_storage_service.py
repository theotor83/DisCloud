"""
Unit tests for the StorageService.

These tests use mocks to avoid actual network calls to storage providers.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from apps.files.services.storage_services import StorageService
from apps.storage_providers.models import StorageProvider


@pytest.mark.django_db
class TestStorageService:
    """Test cases for the StorageService."""

    def test_init_with_discord_provider(self, discord_provider):
        """Test initializing StorageService with a Discord provider."""
        with patch('apps.storage_providers.providers.discord_provider.DiscordStorageProvider') as MockProvider:
            service = StorageService('test_discord')
            
            # Verify the provider was instantiated with the correct config
            MockProvider.assert_called_once_with(discord_provider.config)

    def test_init_with_nonexistent_provider_raises_error(self):
        """Test that initializing with a non-existent provider raises ValueError."""
        with pytest.raises(ValueError, match="Storage provider 'nonexistent' not found"):
            StorageService('nonexistent')

    @pytest.mark.django_db
    def test_init_with_unsupported_platform_raises_error(self):
        """Test that initializing with an unsupported platform raises ValueError."""
        # Create a provider with an unsupported platform
        unsupported = StorageProvider.objects.create(
            name='unsupported_provider',
            platform='UnsupportedPlatform',
            config={}
        )
        
        with pytest.raises(ValueError, match="Unsupported storage provider platform"):
            StorageService('unsupported_provider')

    def test_upload_chunk_delegates_to_provider(self, discord_provider):
        """Test that upload_chunk delegates to the provider's upload_chunk method."""
        with patch('apps.storage_providers.providers.discord_provider.DiscordStorageProvider') as MockProvider:
            mock_instance = MockProvider.return_value
            mock_instance.upload_chunk.return_value = {'message_id': '123456789'}
            
            service = StorageService('test_discord')
            encrypted_chunk = b'encrypted_data_here'
            file_metadata = {'filename': 'test.pdf'}
            
            result = service.upload_chunk(encrypted_chunk, file_metadata)
            
            # Verify the provider's upload_chunk was called
            mock_instance.upload_chunk.assert_called_once_with(encrypted_chunk, file_metadata)
            assert result == {'message_id': '123456789'}

    def test_download_chunk_delegates_to_provider(self, discord_provider):
        """Test that download_chunk delegates to the provider's download_chunk method."""
        with patch('apps.storage_providers.providers.discord_provider.DiscordStorageProvider') as MockProvider:
            mock_instance = MockProvider.return_value
            mock_instance.download_chunk.return_value = b'encrypted_chunk_data'
            
            service = StorageService('test_discord')
            provider_chunk_id = {'message_id': '123456789', 'attachment_id': '987654321'}
            
            result = service.download_chunk(provider_chunk_id)
            
            # Verify the provider's download_chunk was called
            mock_instance.download_chunk.assert_called_once_with(provider_chunk_id)
            assert result == b'encrypted_chunk_data'

    def test_provider_instance_cached(self, discord_provider):
        """Test that the provider instance is cached and reused."""
        with patch('apps.storage_providers.providers.discord_provider.DiscordStorageProvider') as MockProvider:
            service = StorageService('test_discord')
            
            # Access the provider multiple times
            provider1 = service.provider
            provider2 = service.provider
            
            # Should be the same instance
            assert provider1 is provider2
            # Provider should only be instantiated once
            assert MockProvider.call_count == 1


@pytest.mark.unit
class TestStorageServiceIntegration:
    """Integration tests for StorageService with actual provider logic (but mocked network calls)."""

    @pytest.mark.django_db
    def test_full_upload_download_flow(self, discord_provider, mock_aiohttp_response):
        """Test a complete upload and download flow with mocked Discord API."""
        with patch('apps.storage_providers.providers.discord_provider.DiscordStorageProvider') as MockProvider:
            # Setup mock provider behavior
            mock_instance = MockProvider.return_value
            
            # Mock upload returns Discord message ID
            mock_instance.upload_chunk.return_value = {
                'message_id': '987654321',
                'attachment_id': '123456789'
            }
            
            # Mock download returns encrypted data
            expected_data = b'encrypted_chunk_content'
            mock_instance.download_chunk.return_value = expected_data
            
            # Initialize service
            service = StorageService('test_discord')
            
            # Upload a chunk
            encrypted_chunk = b'test_encrypted_data'
            file_metadata = {'filename': 'document.pdf'}
            upload_result = service.upload_chunk(encrypted_chunk, file_metadata)
            
            assert 'message_id' in upload_result
            assert upload_result['message_id'] == '987654321'
            
            # Download the chunk using the returned ID
            downloaded_data = service.download_chunk(upload_result)
            
            assert downloaded_data == expected_data

    @pytest.mark.django_db
    def test_multiple_chunks_upload(self, discord_provider):
        """Test uploading multiple chunks sequentially."""
        with patch('apps.storage_providers.providers.discord_provider.DiscordStorageProvider') as MockProvider:
            mock_instance = MockProvider.return_value
            
            # Mock provider to return different IDs for each chunk
            mock_instance.upload_chunk.side_effect = [
                {'message_id': f'msg_{i}', 'attachment_id': f'att_{i}'}
                for i in range(5)
            ]
            
            service = StorageService('test_discord')
            
            # Upload 5 chunks
            results = []
            for i in range(5):
                chunk = f'chunk_{i}_data'.encode()
                result = service.upload_chunk(chunk, {'filename': 'large_file.bin'})
                results.append(result)
            
            # Verify all chunks got unique IDs
            assert len(results) == 5
            assert all('message_id' in r for r in results)
            message_ids = [r['message_id'] for r in results]
            assert len(set(message_ids)) == 5  # All unique

    @pytest.mark.django_db
    def test_error_handling_on_upload_failure(self, discord_provider):
        """Test that upload errors are properly propagated."""
        with patch('apps.storage_providers.providers.discord_provider.DiscordStorageProvider') as MockProvider:
            mock_instance = MockProvider.return_value
            mock_instance.upload_chunk.side_effect = Exception("Network error")
            
            service = StorageService('test_discord')
            
            with pytest.raises(Exception, match="Network error"):
                service.upload_chunk(b'data', {'filename': 'test.txt'})

    @pytest.mark.django_db
    def test_error_handling_on_download_failure(self, discord_provider):
        """Test that download errors are properly propagated."""
        with patch('apps.storage_providers.providers.discord_provider.DiscordStorageProvider') as MockProvider:
            mock_instance = MockProvider.return_value
            mock_instance.download_chunk.side_effect = Exception("Chunk not found")
            
            service = StorageService('test_discord')
            
            with pytest.raises(Exception, match="Chunk not found"):
                service.download_chunk({'message_id': 'nonexistent'})
