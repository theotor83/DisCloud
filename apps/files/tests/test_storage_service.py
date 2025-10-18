"""
Unit tests for the StorageService.

These tests use mocks to avoid actual network calls to storage providers.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from apps.files.services.storage_service import StorageService
from apps.storage_providers.models import StorageProvider
from apps.storage_providers.providers.discord.discord_provider import DiscordStorageProvider


@pytest.mark.django_db
class TestStorageService:
    """Test cases for the StorageService."""

    def test_init_with_discord_provider(self, discord_provider):
        """Test initializing StorageService with a Discord provider."""
        service = StorageService('test_discord', skip_validation=True)
        
        # Verify the service was created successfully
        assert service.provider_name == 'test_discord'
        assert service.provider is not None

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
        with patch.object(DiscordStorageProvider, 'upload_chunk', return_value={'message_id': '123456789'}) as mock_upload:
            service = StorageService('test_discord', skip_validation=True)
            encrypted_chunk = b'encrypted_data_here'
            file_metadata = {'filename': 'test.pdf'}
            
            result = service.upload_chunk(encrypted_chunk, file_metadata)
            
            # Verify the provider's upload_chunk was called
            mock_upload.assert_called_once_with(encrypted_chunk, file_metadata)
            assert result == {'message_id': '123456789'}

    def test_download_chunk_delegates_to_provider(self, discord_provider):
        """Test that download_chunk delegates to the provider's download_chunk method."""
        with patch.object(DiscordStorageProvider, 'download_chunk', return_value=b'encrypted_chunk_data') as mock_download:
            service = StorageService('test_discord', skip_validation=True)
            provider_chunk_metadata = {'message_id': '123456789', 'attachment_id': '987654321'}
            file_metadata = {'filename': 'test.pdf'}
            
            result = service.download_chunk(provider_chunk_metadata, file_metadata)
            
            # Verify the provider's download_chunk was called
            mock_download.assert_called_once_with(provider_chunk_metadata, file_metadata)
            assert result == b'encrypted_chunk_data'

    def test_provider_instance_cached(self, discord_provider):
        """Test that the provider instance is cached and reused."""
        service = StorageService('test_discord', skip_validation=True)
        
        # Access the provider multiple times
        provider1 = service.provider
        provider2 = service.provider
        
        # Should be the same instance
        assert provider1 is provider2


@pytest.mark.unit
class TestStorageServiceIntegration:
    """Integration tests for StorageService with actual provider logic (but mocked network calls)."""

    @pytest.mark.django_db
    def test_full_upload_download_flow(self, discord_provider, mock_aiohttp_response):
        """Test a complete upload and download flow with mocked Discord API."""
        with patch.object(DiscordStorageProvider, 'upload_chunk', return_value={'message_id': '987654321', 'attachment_id': '123456789'}) as mock_upload:
            with patch.object(DiscordStorageProvider, 'download_chunk', return_value=b'encrypted_chunk_content') as mock_download:
                # Initialize service
                service = StorageService('test_discord', skip_validation=True)
                
                # Upload a chunk
                encrypted_chunk = b'test_encrypted_data'
                file_metadata = {'filename': 'document.pdf'}
                upload_result = service.upload_chunk(encrypted_chunk, file_metadata)
                
                assert 'message_id' in upload_result
                assert upload_result['message_id'] == '987654321'
                
                # Download the chunk using the returned ID
                downloaded_data = service.download_chunk(upload_result, file_metadata)
                
                assert downloaded_data == b'encrypted_chunk_content'

    @pytest.mark.django_db
    def test_multiple_chunks_upload(self, discord_provider):
        """Test uploading multiple chunks sequentially."""
        # Mock provider to return different IDs for each chunk
        side_effect_values = [
            {'message_id': f'msg_{i}', 'attachment_id': f'att_{i}'}
            for i in range(5)
        ]
        
        with patch.object(DiscordStorageProvider, 'upload_chunk', side_effect=side_effect_values):
            service = StorageService('test_discord', skip_validation=True)
            
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
        with patch.object(DiscordStorageProvider, 'upload_chunk', side_effect=Exception("Network error")):
            service = StorageService('test_discord', skip_validation=True)
            
            with pytest.raises(Exception, match="Network error"):
                service.upload_chunk(b'data', {'filename': 'test.txt'})

    @pytest.mark.django_db
    def test_error_handling_on_download_failure(self, discord_provider):
        """Test that download errors are properly propagated."""
        with patch.object(DiscordStorageProvider, 'download_chunk', side_effect=Exception("Chunk not found")):
            service = StorageService('test_discord', skip_validation=True)
            
            with pytest.raises(Exception, match="Chunk not found"):
                service.download_chunk({'message_id': 'nonexistent'}, {'filename': 'test.pdf'})
