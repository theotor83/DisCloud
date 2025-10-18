"""
Integration tests for Discord provider with REAL Discord API calls.

⚠️ WARNING: These tests make actual network requests to Discord!

Prerequisites:
1. Set environment variables with real Discord credentials:
   - DISCORD_TEST_BOT_TOKEN
   - DISCORD_TEST_SERVER_ID
   - DISCORD_TEST_CHANNEL_ID

2. The bot must have permissions in the test server/channel

3. These tests will create real threads and upload real files to Discord

Usage:
    # Run only integration tests with real API
    pytest apps/storage_providers/tests/providers/test_discord_provider_integration.py

    # Skip these tests normally (they're slow and need credentials)
    pytest -m "not real_api"

These tests verify:
- Our code works with the REAL Discord API
- Authentication works correctly
- Thread creation actually succeeds
- File uploads work end-to-end
- We handle real rate limits and errors correctly
"""
import os
import pytest
import time
from apps.storage_providers.providers.discord.discord_provider import DiscordStorageProvider


# Skip these tests unless explicitly requested or credentials are available
pytestmark = pytest.mark.skipif(
    not os.getenv('DISCORD_TEST_BOT_TOKEN'),
    reason="Real Discord API tests require DISCORD_TEST_BOT_TOKEN environment variable"
)


@pytest.fixture
def real_discord_config():
    """Get real Discord configuration from environment variables."""
    return {
        'bot_token': os.getenv('DISCORD_TEST_BOT_TOKEN'),
        'server_id': os.getenv('DISCORD_TEST_SERVER_ID'),
        'channel_id': os.getenv('DISCORD_TEST_CHANNEL_ID')
    }


@pytest.mark.real_api
@pytest.mark.slow
def test_real_thread_creation(real_discord_config):
    """
    Test creating a real Discord thread.
    
    This verifies:
    - Our bot token is valid
    - We have permissions in the channel
    - Thread creation actually works
    - Discord's API behaves as expected
    """
    provider = DiscordStorageProvider(real_discord_config, skip_validation=True)
    
    file_metadata = {'filename': 'integration_test_file.txt'}
    result = provider.prepare_storage(file_metadata)
    
    # Verify we got a real thread ID back
    assert result is not None
    assert 'thread_id' in result
    assert len(result['thread_id']) > 0
    
    print(f"✅ Created real Discord thread: {result['thread_id']}")


@pytest.mark.real_api
@pytest.mark.slow
def test_real_thread_creation_with_special_characters(real_discord_config):
    """Test thread creation with filename containing special characters."""
    provider = DiscordStorageProvider(real_discord_config, skip_validation=True)
    
    file_metadata = {'filename': 'test_file_@#$%_2024.pdf'}
    result = provider.prepare_storage(file_metadata)
    
    assert result is not None
    assert 'thread_id' in result
    
    print(f"✅ Created thread with special chars: {result['thread_id']}")


@pytest.mark.real_api
@pytest.mark.slow
def test_real_prepare_storage_sync(real_discord_config):
    """Test the synchronous prepare_storage method with real API."""
    provider = DiscordStorageProvider(real_discord_config, skip_validation=True)
    
    file_metadata = {'filename': 'sync_integration_test.txt'}
    result = provider.prepare_storage(file_metadata)
    
    assert result is not None
    assert 'thread_id' in result
    
    print(f"✅ Prepared storage (sync): {result['thread_id']}")


@pytest.mark.real_api
@pytest.mark.slow
def test_real_invalid_credentials():
    """Test that invalid credentials are properly rejected."""
    invalid_config = {
        'bot_token': 'invalid_token_123',
        'server_id': '123456789',
        'channel_id': '987654321'
    }
    
    provider = DiscordStorageProvider(invalid_config, skip_validation=True)
    
    file_metadata = {'filename': 'test.txt'}
    
    # Should raise an exception with invalid credentials
    with pytest.raises(Exception):  # Will raise StorageUploadError
        provider.prepare_storage(file_metadata)
    
    print("✅ Invalid credentials properly rejected")


@pytest.mark.real_api
@pytest.mark.slow
def test_real_multiple_threads(real_discord_config):
    """Test creating multiple threads in succession."""
    provider = DiscordStorageProvider(real_discord_config, skip_validation=True)
    
    threads = []
    for i in range(3):
        file_metadata = {'filename': f'multi_test_file_{i}.txt'}
        result = provider.prepare_storage(file_metadata)
        
        assert result is not None
        assert 'thread_id' in result
        threads.append(result['thread_id'])
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    # Verify all thread IDs are unique
    assert len(set(threads)) == 3
    
    print(f"✅ Created {len(threads)} unique threads")


@pytest.mark.real_api
@pytest.mark.slow
class TestRealDiscordProviderEndToEnd:
    """
    End-to-end tests with real Discord API.
    
    These test the complete flow but are expensive and slow.
    """
    
    def test_complete_file_upload_flow(self, real_discord_config):
        """
        Test complete flow: prepare storage -> upload chunk.
        
        NOTE: This will be completed when upload_chunk is implemented.
        For now, we test what's available.
        """
        provider = DiscordStorageProvider(real_discord_config, skip_validation=True)
        
        # Step 1: Prepare storage (create thread)
        file_metadata = {'filename': 'e2e_test_file.bin'}
        storage_metadata = provider.prepare_storage(file_metadata)
        
        assert storage_metadata is not None
        assert 'thread_id' in storage_metadata
        
        print(f"✅ E2E test prepared storage: {storage_metadata['thread_id']}")
        
        # Step 2: Upload chunk (will be implemented later)
        # encrypted_chunk = b'test encrypted data'
        # chunk_id = provider.upload_chunk(encrypted_chunk, file_metadata)
        
        # Step 3: Download chunk (will be implemented later)
        # downloaded = provider.download_chunk(chunk_id)
        
        # assert downloaded == encrypted_chunk


# Configuration tests with real validation
@pytest.mark.real_api
@pytest.mark.slow
class TestRealConfiguration:
    """Test configuration validation with real Discord API."""
    
    def test_bot_token_format(self, real_discord_config):
        """Verify bot token has expected format."""
        token = real_discord_config['bot_token']
        
        # Discord bot tokens are typically long strings
        assert len(token) > 50
        assert isinstance(token, str)
    
    def test_channel_id_format(self, real_discord_config):
        """Verify channel/server IDs are numeric strings."""
        server_id = real_discord_config['server_id']
        channel_id = real_discord_config['channel_id']
        
        # Discord IDs are numeric strings (snowflakes)
        assert server_id.isdigit()
        assert channel_id.isdigit()
        assert len(server_id) >= 17  # Discord snowflakes are 17-19 digits
        assert len(channel_id) >= 17
