"""
Shared pytest fixtures for the DisCloud project.
"""
import pytest
from unittest.mock import Mock, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.storage_providers.models import StorageProvider
from apps.files.models import File, Chunk
from apps.storage_providers.providers import PLATFORM_DISCORD


@pytest.fixture
def mock_discord_config():
    """Returns a mock Discord provider configuration."""
    return {
        'bot_token': 'test_bot_token_123456',
        'server_id': '123456789012345678',
        'channel_id': '987654321098765432'
    }


@pytest.fixture
@pytest.mark.django_db
def discord_provider(mock_discord_config):
    """Creates a Discord StorageProvider in the test database."""
    provider = StorageProvider.objects.create(
        name='test_discord',
        platform=PLATFORM_DISCORD,
        config=mock_discord_config
    )
    return provider


@pytest.fixture
def sample_encryption_key():
    """Returns a sample encryption key for testing."""
    return b'0' * 32  # 32 bytes for AES-256


@pytest.fixture
def sample_file_data():
    """Returns sample binary file data for testing."""
    return b'This is test file content for encryption and upload testing.' * 100


@pytest.fixture
def uploaded_file():
    """Returns a Django UploadedFile for testing views."""
    return SimpleUploadedFile(
        "test_file.txt",
        b"Test file content",
        content_type="text/plain"
    )


@pytest.fixture
@pytest.mark.django_db
def sample_file(discord_provider, sample_encryption_key):
    """Creates a sample File object in the test database."""
    file_obj = File.objects.create(
        original_filename='test_document.pdf',
        encrypted_filename='abc123def456.enc',
        description='A test file for unit testing',
        encryption_key=sample_encryption_key,
        storage_provider=discord_provider,
        storage_metadata={'thread_id': '111222333444555666'}
    )
    return file_obj


@pytest.fixture
@pytest.mark.django_db
def file_with_chunks(sample_file):
    """Creates a file with multiple chunks for testing."""
    chunks = []
    for i in range(3):
        chunk = Chunk.objects.create(
            file=sample_file,
            chunk_order=i,
            provider_chunk_id={'message_id': f'msg_{i}', 'attachment_id': f'att_{i}'}
        )
        chunks.append(chunk)
    return sample_file, chunks


@pytest.fixture
def mock_aiohttp_response():
    """Creates a mock aiohttp response for testing async HTTP calls."""
    mock_response = MagicMock()
    mock_response.status = 201
    mock_response.json = MagicMock(return_value={'id': '123456789'})
    mock_response.text = MagicMock(return_value='Success')
    return mock_response


@pytest.fixture
def mock_storage_service():
    """Returns a mock StorageService for testing without actual uploads."""
    mock_service = Mock()
    mock_service.upload_chunk.return_value = {'message_id': 'test_msg_123'}
    mock_service.download_chunk.return_value = b'encrypted_data'
    return mock_service


@pytest.fixture
def mock_encryption_service():
    """Returns a mock EncryptionService for testing without actual encryption."""
    mock_service = Mock()
    mock_service.generate_key.return_value = b'0' * 32
    mock_service.encrypt_chunk.return_value = b'encrypted_chunk_data'
    mock_service.decrypt_chunk.return_value = b'decrypted_chunk_data'
    return mock_service


@pytest.fixture
def mock_discord_validator():
    """Returns a mock Discord validator that always validates successfully."""
    mock = Mock()
    mock.validate = Mock(return_value=True)
    return mock
