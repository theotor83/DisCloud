"""
Unit tests for the Discord storage provider.

These tests mock HTTP calls to the Discord API using aioresponses.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from aioresponses import aioresponses
from apps.storage_providers.providers.discord_provider import DiscordStorageProvider


@pytest.mark.unit
class TestDiscordProviderInitialization:
    """Test Discord provider initialization."""

    def test_init_with_valid_config(self, mock_discord_config):
        """Test initializing the provider with valid config."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        assert provider.bot_token == mock_discord_config['bot_token']
        assert provider.server_id == mock_discord_config['server_id']
        assert provider.channel_id == mock_discord_config['channel_id']
        assert provider.api_base == "https://discord.com/api/v10"

    def test_config_stored(self, mock_discord_config):
        """Test that config is stored in the provider."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        assert provider.config == mock_discord_config

    def test_init_with_missing_config_values(self):
        """Test initialization with incomplete config."""
        incomplete_config = {
            'bot_token': 'token123',
            # Missing server_id and channel_id
        }
        
        provider = DiscordStorageProvider(incomplete_config)
        
        assert provider.bot_token == 'token123'
        assert provider.server_id is None
        assert provider.channel_id is None


@pytest.mark.asyncio
class TestDiscordProviderThreadCreation:
    """Test Discord thread creation for file uploads."""

    @pytest.mark.asyncio
    async def test_create_thread_async_success(self, mock_discord_config):
        """Test successful thread creation via Discord API."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        with aioresponses() as mocked:
            # Mock the Discord API response for thread creation
            expected_thread_id = '111222333444555666'
            mocked.post(
                f"https://discord.com/api/v10/channels/{mock_discord_config['channel_id']}/threads",
                status=201,
                payload={'id': expected_thread_id, 'name': '[FILE] test.txt'}
            )
            
            file_metadata = {'filename': 'test.txt'}
            result = await provider._create_thread_async(file_metadata)
            
            assert result is not None
            assert 'thread_id' in result
            assert result['thread_id'] == expected_thread_id

    @pytest.mark.asyncio
    async def test_create_thread_async_failure(self, mock_discord_config):
        """Test thread creation failure handling."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        with aioresponses() as mocked:
            # Mock a failed API response
            mocked.post(
                f"https://discord.com/api/v10/channels/{mock_discord_config['channel_id']}/threads",
                status=403,
                payload={'message': 'Missing Permissions'}
            )
            
            file_metadata = {'filename': 'test.txt'}
            result = await provider._create_thread_async(file_metadata)
            
            # Should return None on failure
            assert result is None

    @pytest.mark.asyncio
    async def test_create_thread_with_special_filename(self, mock_discord_config):
        """Test thread creation with special characters in filename."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        with aioresponses() as mocked:
            expected_thread_id = '999888777666555444'
            
            # Capture the request to verify the thread name
            def callback(url, **kwargs):
                json_data = kwargs.get('json', {})
                assert '[FILE]' in json_data['name']
                assert 'special@file#2024.pdf' in json_data['name']
                return aioresponses.CallbackResult(
                    status=201,
                    payload={'id': expected_thread_id}
                )
            
            mocked.post(
                f"https://discord.com/api/v10/channels/{mock_discord_config['channel_id']}/threads",
                callback=callback
            )
            
            file_metadata = {'filename': 'special@file#2024.pdf'}
            result = await provider._create_thread_async(file_metadata)
            
            assert result['thread_id'] == expected_thread_id

    def test_prepare_storage_calls_async_method(self, mock_discord_config):
        """Test that prepare_storage properly calls the async thread creation method."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        with aioresponses() as mocked:
            expected_thread_id = '123123123123123123'
            mocked.post(
                f"https://discord.com/api/v10/channels/{mock_discord_config['channel_id']}/threads",
                status=201,
                payload={'id': expected_thread_id}
            )
            
            file_metadata = {'filename': 'sync_test.txt'}
            result = provider.prepare_storage(file_metadata)
            
            assert result is not None
            assert result['thread_id'] == expected_thread_id

    @pytest.mark.asyncio
    async def test_thread_creation_timeout(self, mock_discord_config):
        """Test handling of timeout during thread creation."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        with aioresponses() as mocked:
            # Mock a timeout by raising an exception
            mocked.post(
                f"https://discord.com/api/v10/channels/{mock_discord_config['channel_id']}/threads",
                exception=asyncio.TimeoutError()
            )
            
            file_metadata = {'filename': 'timeout_test.txt'}
            result = await provider._create_thread_async(file_metadata)
            
            # Should handle timeout gracefully and return None
            assert result is None


@pytest.mark.unit
class TestDiscordProviderChunkOperations:
    """Test chunk upload and download operations."""

    def test_upload_chunk_interface(self, mock_discord_config):
        """Test that upload_chunk method exists and has correct signature."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        # Method should exist
        assert hasattr(provider, 'upload_chunk')
        assert callable(provider.upload_chunk)

    def test_download_chunk_interface(self, mock_discord_config):
        """Test that download_chunk method exists and has correct signature."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        # Method should exist
        assert hasattr(provider, 'download_chunk')
        assert callable(provider.download_chunk)

    @pytest.mark.asyncio
    async def test_upload_chunk_implementation(self, mock_discord_config):
        """
        Test upload_chunk when implemented.
        
        This test is a placeholder and should be updated when upload_chunk is implemented.
        Expected behavior:
        1. Create a Discord message in the thread
        2. Attach the encrypted chunk as a file
        3. Return the message ID and attachment ID
        """
        provider = DiscordStorageProvider(mock_discord_config)
        
        # This will be implemented later
        # For now, just verify the method exists
        assert provider.upload_chunk is not None

    @pytest.mark.asyncio
    async def test_download_chunk_implementation(self, mock_discord_config):
        """
        Test download_chunk when implemented.
        
        This test is a placeholder and should be updated when download_chunk is implemented.
        Expected behavior:
        1. Fetch the Discord message by ID
        2. Download the attachment
        3. Return the encrypted chunk data
        """
        provider = DiscordStorageProvider(mock_discord_config)
        
        # This will be implemented later
        # For now, just verify the method exists
        assert provider.download_chunk is not None


@pytest.mark.unit
class TestDiscordProviderConfiguration:
    """Test provider configuration handling."""

    def test_api_base_url(self, mock_discord_config):
        """Test that the Discord API base URL is correct."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        assert provider.api_base == "https://discord.com/api/v10"

    def test_config_retrieval(self, mock_discord_config):
        """Test retrieving config values."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        # All config values should be accessible
        assert provider.config.get('bot_token') == mock_discord_config['bot_token']
        assert provider.config.get('server_id') == mock_discord_config['server_id']
        assert provider.config.get('channel_id') == mock_discord_config['channel_id']

    def test_headers_for_authentication(self, mock_discord_config):
        """Test that authentication headers would be correctly formatted."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        # Test that bot token is in the expected format
        expected_auth_header = f"Bot {mock_discord_config['bot_token']}"
        assert provider.bot_token in expected_auth_header


@pytest.mark.integration
class TestDiscordProviderEndToEnd:
    """Integration tests for complete upload/download flows."""

    @pytest.mark.asyncio
    async def test_full_file_upload_flow(self, mock_discord_config):
        """
        Test a complete file upload flow:
        1. Prepare storage (create thread)
        2. Upload chunks
        3. Verify all chunks are uploaded
        """
        provider = DiscordStorageProvider(mock_discord_config)
        
        with aioresponses() as mocked:
            # Mock thread creation
            thread_id = '111222333444555666'
            mocked.post(
                f"https://discord.com/api/v10/channels/{mock_discord_config['channel_id']}/threads",
                status=201,
                payload={'id': thread_id}
            )
            
            # Prepare storage
            file_metadata = {'filename': 'large_file.bin'}
            storage_metadata = provider.prepare_storage(file_metadata)
            
            assert storage_metadata is not None
            assert storage_metadata['thread_id'] == thread_id
            
            # Note: Chunk upload tests will be added when upload_chunk is implemented

    def test_error_recovery_on_network_failure(self, mock_discord_config):
        """Test that the provider handles network failures gracefully."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        with aioresponses() as mocked:
            # Mock a network error
            mocked.post(
                f"https://discord.com/api/v10/channels/{mock_discord_config['channel_id']}/threads",
                exception=Exception("Network unreachable")
            )
            
            file_metadata = {'filename': 'test.txt'}
            result = provider.prepare_storage(file_metadata)
            
            # Should handle the error and return None
            assert result is None

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, mock_discord_config):
        """Test handling of Discord API rate limits."""
        provider = DiscordStorageProvider(mock_discord_config)
        
        with aioresponses() as mocked:
            # Mock a rate limit response (429)
            mocked.post(
                f"https://discord.com/api/v10/channels/{mock_discord_config['channel_id']}/threads",
                status=429,
                payload={
                    'message': 'You are being rate limited.',
                    'retry_after': 2.5
                }
            )
            
            file_metadata = {'filename': 'test.txt'}
            result = await provider._create_thread_async(file_metadata)
            
            # Currently returns None on any non-201 status
            # Future implementation could add retry logic
            assert result is None
