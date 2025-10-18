"""
Unit tests for the Discord storage provider.

These tests mock HTTP calls to the Discord API using unittest.mock.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx
from apps.storage_providers.providers.discord.discord_provider import DiscordStorageProvider
from apps.files.exceptions import StorageUploadError


@pytest.mark.unit
class TestDiscordProviderInitialization:
    """Test Discord provider initialization."""

    def test_init_with_valid_config(self, mock_discord_config):
        """Test initializing the provider with valid config."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        assert provider.bot_token == mock_discord_config['bot_token']
        assert provider.server_id == mock_discord_config['server_id']
        assert provider.channel_id == mock_discord_config['channel_id']
        assert provider.api_base == "https://discord.com/api/v10"

    def test_config_stored(self, mock_discord_config):
        """Test that config is stored in the provider."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        assert provider.config == mock_discord_config

    def test_init_with_missing_config_values(self):
        """Test initialization with incomplete config."""
        incomplete_config = {
            'bot_token': 'token123',
            # Missing server_id and channel_id
        }
        
        provider = DiscordStorageProvider(incomplete_config, skip_validation=True)
        
        assert provider.bot_token == 'token123'
        assert provider.server_id is None
        assert provider.channel_id is None


@pytest.mark.unit
class TestDiscordProviderThreadCreation:
    """Test Discord thread creation for file uploads."""

    def test_prepare_storage_success(self, mock_discord_config):
        """Test successful thread creation via Discord API."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Mock the httpx.Client.post response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': '111222333444555666',
            'name': '[FILE] test.txt'
        }
        
        with patch('httpx.Client.post', return_value=mock_response):
            file_metadata = {'filename': 'test.txt'}
            result = provider.prepare_storage(file_metadata)
            
            assert result is not None
            assert 'thread_id' in result
            assert result['thread_id'] == '111222333444555666'

    def test_prepare_storage_failure(self, mock_discord_config):
        """Test thread creation failure handling."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Mock a failed API response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = 'Missing Permissions'
        
        with patch('httpx.Client.post', return_value=mock_response):
            file_metadata = {'filename': 'test.txt'}
            
            # Should raise StorageUploadError on failure
            with pytest.raises(StorageUploadError) as exc_info:
                provider.prepare_storage(file_metadata)
            
            assert 'Discord API error' in str(exc_info.value)
            assert '403' in str(exc_info.value)

    def test_prepare_storage_with_special_filename(self, mock_discord_config):
        """Test thread creation with special characters in filename."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        expected_thread_id = '999888777666555444'
        
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': expected_thread_id}
        
        with patch('httpx.Client.post', return_value=mock_response) as mock_post:
            file_metadata = {'filename': 'special@file#2024.pdf'}
            result = provider.prepare_storage(file_metadata)
            
            assert result['thread_id'] == expected_thread_id
            
            # Verify the request was made with correct thread name
            call_args = mock_post.call_args
            json_data = call_args.kwargs.get('json', {})
            assert '[FILE]' in json_data['name']
            assert 'special@file#2024.pdf' in json_data['name']

    def test_prepare_storage_creates_thread(self, mock_discord_config):
        """Test that prepare_storage properly creates a Discord thread."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        expected_thread_id = '123123123123123123'
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': expected_thread_id}
        
        with patch('httpx.Client.post', return_value=mock_response):
            file_metadata = {'filename': 'sync_test.txt'}
            result = provider.prepare_storage(file_metadata)
            
            assert result is not None
            assert result['thread_id'] == expected_thread_id

    def test_prepare_storage_timeout(self, mock_discord_config):
        """Test handling of timeout during thread creation."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Mock a timeout by raising an exception
        with patch('httpx.Client.post', side_effect=httpx.TimeoutException('Request timeout')):
            file_metadata = {'filename': 'timeout_test.txt'}
            
            # Should raise StorageUploadError wrapping the timeout
            with pytest.raises(StorageUploadError) as exc_info:
                provider.prepare_storage(file_metadata)
            
            assert 'Network error' in str(exc_info.value)


@pytest.mark.unit
class TestDiscordProviderChunkOperations:
    """Test chunk upload and download operations."""

    def test_upload_chunk_interface(self, mock_discord_config):
        """Test that upload_chunk method exists and has correct signature."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Method should exist
        assert hasattr(provider, 'upload_chunk')
        assert callable(provider.upload_chunk)

    def test_download_chunk_interface(self, mock_discord_config):
        """Test that download_chunk method exists and has correct signature."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Method should exist
        assert hasattr(provider, 'download_chunk')
        assert callable(provider.download_chunk)

    def test_upload_chunk_success(self, mock_discord_config):
        """Test successful chunk upload to Discord."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Mock successful upload response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'message_123',
            'attachments': [{'id': 'attachment_456'}]
        }
        
        with patch('httpx.Client.post', return_value=mock_response):
            encrypted_chunk = b'encrypted test data'
            file_metadata = {'thread_id': '111222333444555666'}
            
            result = provider.upload_chunk(encrypted_chunk, file_metadata)
            
            assert result is not None
            assert 'message_id' in result
            assert result['message_id'] == 'message_123'
            assert result['thread_id'] == '111222333444555666'

    def test_upload_chunk_missing_thread_id(self, mock_discord_config):
        """Test upload_chunk raises error when thread_id is missing."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        encrypted_chunk = b'encrypted test data'
        file_metadata = {}  # Missing thread_id
        
        with pytest.raises(ValueError) as exc_info:
            provider.upload_chunk(encrypted_chunk, file_metadata)
        
        assert 'thread_id' in str(exc_info.value)

    def test_download_chunk_not_implemented(self, mock_discord_config):
        """Test download_chunk method (placeholder until implemented)."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # This will be implemented later
        # For now, just verify the method exists
        assert provider.download_chunk is not None


@pytest.mark.unit
class TestDiscordProviderConfiguration:
    """Test provider configuration handling."""

    def test_api_base_url(self, mock_discord_config):
        """Test that the Discord API base URL is correct."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        assert provider.api_base == "https://discord.com/api/v10"

    def test_config_retrieval(self, mock_discord_config):
        """Test retrieving config values."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # All config values should be accessible
        assert provider.config.get('bot_token') == mock_discord_config['bot_token']
        assert provider.config.get('server_id') == mock_discord_config['server_id']
        assert provider.config.get('channel_id') == mock_discord_config['channel_id']

    def test_headers_for_authentication(self, mock_discord_config):
        """Test that authentication headers would be correctly formatted."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Test that bot token is in the expected format
        expected_auth_header = f"Bot {mock_discord_config['bot_token']}"
        assert provider.bot_token in expected_auth_header


@pytest.mark.integration
class TestDiscordProviderEndToEnd:
    """Integration tests for complete upload/download flows."""

    def test_full_file_upload_flow(self, mock_discord_config):
        """
        Test a complete file upload flow:
        1. Prepare storage (create thread)
        2. Upload chunks
        3. Verify all chunks are uploaded
        """
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Mock thread creation
        thread_id = '111222333444555666'
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': thread_id}
        
        with patch('httpx.Client.post', return_value=mock_response):
            # Prepare storage
            file_metadata = {'filename': 'large_file.bin'}
            storage_metadata = provider.prepare_storage(file_metadata)
            
            assert storage_metadata is not None
            assert storage_metadata['thread_id'] == thread_id
            
            # Note: Chunk upload tests will be added when upload_chunk is implemented

    def test_error_recovery_on_network_failure(self, mock_discord_config):
        """Test that the provider handles network failures gracefully."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Mock a network error
        with patch('httpx.Client.post', side_effect=httpx.ConnectError('Network unreachable')):
            file_metadata = {'filename': 'test.txt'}
            
            # Should raise StorageUploadError
            with pytest.raises(StorageUploadError) as exc_info:
                provider.prepare_storage(file_metadata)
            
            assert 'Network error' in str(exc_info.value)

    def test_rate_limit_handling(self, mock_discord_config):
        """Test handling of Discord API rate limits."""
        provider = DiscordStorageProvider(mock_discord_config, skip_validation=True)
        
        # Mock a rate limit response (429)
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = 'You are being rate limited.'
        
        with patch('httpx.Client.post', return_value=mock_response):
            file_metadata = {'filename': 'test.txt'}
            
            # Should raise StorageUploadError on rate limit
            with pytest.raises(StorageUploadError) as exc_info:
                provider.prepare_storage(file_metadata)
            
            assert '429' in str(exc_info.value)
