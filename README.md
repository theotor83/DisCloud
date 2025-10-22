# DisCloud

**Secure, encrypted file storage system using external platforms as cloud storage**

DisCloud is a Django-based application that enables secure file storage by splitting files into chunks, encrypting them, and distributing them across external storage platforms (currently Discord). Files are encrypted before leaving your server and decrypted on-demand during downloads.

**DISCLAIMER:** This project was created primarily for educational purposes. Using consumer or third‑party platforms (Discord for example) as cloud storage is frequently against those platforms’ Terms of Service and can result in account suspension, bans, or other enforcement actions. The project authors and maintainers are not responsible for any consequences arising from misuse of this software.

Please note the following before experimenting:

- This software is provided "as‑is" with no warranties. Use at your own risk.
- For experiments, prefer isolated test accounts. Avoid using personal or shared accounts/servers.
- Check applicable regulations and laws before storing third‑party or personal data. If in doubt

Issues, questions, or contributions are welcome via the project’s GitHub Issues and Pull Requests. Use common sense and act responsibly when experimenting with external platforms.

Also note that this project is still in very early development. The core functionality is working, but many features still need to be implemented or improved (i.e. make the frontend better as it is currently made by AI, make everything accessible through the web UI...).

---

## Table of Contents

- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Storage Providers](#-storage-providers)
- [Development](#-development)
- [Testing](#-testing)
- [API Reference](#-api-reference)
- [Security](#-security)
- [Contributing](#-contributing)

---

## Architecture

DisCloud follows a **three-layer architecture** for clean separation of concerns:

### 1. **Service Layer** (`apps/files/services/`)

Business logic and orchestration:

- **FileService**: Orchestrates file lifecycle (upload, download, deletion)
- **EncryptionService**: Handles AES-256-CBC encryption/decryption with per-chunk IVs
- **StorageService**: Abstracts storage provider interactions

### 2. **Repository Pattern** (`repository.py`)

Data access abstraction:

- All Django ORM operations go through repository interfaces
- Enables easy mocking in tests
- `FileRepositoryDjango`, `StorageProviderRepositoryDjango`

**NOTE:** This layer does not do a lot right and would need to be expanded in the future.

### 3. **Provider Plugin System** (`apps/storage_providers/providers/`)

Pluggable storage backends:

- **BaseStorageProvider**: Abstract interface for all providers
- **DiscordStorageProvider**: Stores chunks as Discord message attachments
- Easy to extend with new platforms (Telegram, OneDrive, etc.)

```
┌─────────────────────────────────────────────────────────────┐
│                        Views Layer                          │
│              (Upload, Download, List Files)                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Service Layer                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │FileService  │  │Encryption    │  │Storage       │      │
│  │             │─▶│Service       │  │Service       │      │
│  └─────────────┘  └──────────────┘  └──────┬───────┘      │
└───────────────────────────────────────────┼───────────────┘
                            │               │
┌───────────────────────────▼───────────────▼───────────────┐
│                  Repository Layer                          │
│         (FileRepository, ProviderRepository)               │
└───────────────────────────┬────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                   Database (SQLite)                         │
│              (File, Chunk, StorageProvider)                 │
└────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Discord Bot Token (for Discord storage provider)
- Git

### Step 1: Clone the Repository

```powershell
git clone https://github.com/yourusername/discloud.git
cd discloud
```

### Step 2: Create Virtual Environment

```powershell
python -m venv discloud.venv
.\discloud.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

Create a `.env` file in the project root:

```ini
# Django Configuration
SECRET_KEY=your-django-secret-key-here

# Discord Provider Configuration
BOT_TOKEN=your-discord-bot-token
SERVER_ID=your-discord-server-id
CHANNEL_ID=your-discord-channel-id
```

**How to get Discord credentials:**

1. Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a bot and copy the **Bot Token**
3. Enable "Message Content Intent" in Bot settings
4. Get your Server ID (enable Developer Mode in Discord settings, right-click server → Copy ID)
5. Get your Channel ID (right-click channel → Copy ID)
6. Invite bot with permissions: `Send Messages`, `Read Message History`, `Create Public Threads`

### Step 5: Initialize Database

```powershell
python manage.py migrate
```

### Step 6: Create Storage Provider

```powershell
python manage.py create_default_provider
```

### Step 7: Create Admin User (Optional)

```powershell
python manage.py createsuperuser
```

---

## Configuration

### Settings Overview

Key settings in `discloud/settings.py`:

```python
# File Upload Settings
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Database (SQLite by default)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {...},
        'file': {'filename': BASE_DIR / 'debug.log', ...},
    },
    'loggers': {
        'apps.files': {'level': 'DEBUG', ...},
        'apps.storage_providers': {'level': 'DEBUG', ...},
    },
}
```

### Chunk Size Configuration

Each storage provider defines its maximum chunk size:

- **DiscordStorageProvider**: 8 MB by default, customizable

---

## Usage

### Starting the Development Server

**Option 1: Django Dev Server**
```powershell
python manage.py runserver
```

**Option 2: Daphne (ASGI Server)**
```powershell
python -m daphne -b 127.0.0.1 -p 8000 discloud.asgi:application
```

Visit: `http://127.0.0.1:8000`

### Web Interface

#### 1. Upload Files
Navigate to `/upload/` and select a file to upload.

#### 2. View All Files
Navigate to `/files/` to see all uploaded files with download links.

#### 3. Download Files
Click download on any file. The system will:
- Fetch encrypted chunks from storage provider
- Decrypt chunks on-the-fly
- Stream directly to your browser

#### 4. Admin Interface
Visit `/admin/` to manage files, chunks, and storage providers.

---

## Storage Providers

### Currently Supported

#### 1. **Discord** (`DiscordStorageProvider`)

Stores file chunks as Discord message attachments.

**Features:**
- Public thread creation for organization
- 8 MB chunks (safe for Discord's 10 MB limit)
- Automatic retry on rate limits
- Message ID tracking for retrieval

**Configuration:**
```python
{
    "bot_token": "your_bot_token",
    "server_id": "123456789",
    "channel_id": "987654321",
    "max_chunk_size": "8388640", # Optional, defaults to 8MB
}
```

### Adding a New Provider

**Step 1:** Create provider class in `apps/storage_providers/providers/`

```python
# apps/storage_providers/providers/telegram/telegram_provider.py

from ..base import BaseStorageProvider

class TelegramStorageProvider(BaseStorageProvider):
    def __init__(self, config: dict, skip_validation: bool = False):
        super().__init__(config)
        self.bot_token = config['bot_token']
        self.chat_id = config['chat_id']
        self.max_chunk_size = 20 * 1024 * 1024  # 20 MB
        
        if not skip_validation:
            self._validate_config() # Or use a Validator class
    
    def _validate_config(self):
        """Validate configuration by testing API connection"""
        # Implement validation logic
        pass
    
    def prepare_storage(self, file_metadata: dict) -> dict:
        """Optional: Create storage container"""
        # Create Telegram channel/topic if needed
        return {"chat_id": self.chat_id}
    
    def upload_chunk(self, chunk_data: bytes, storage_context: dict) -> dict:
        """Upload chunk to Telegram"""
        # Implement upload logic
        return {"message_id": "123456"}
    
    def download_chunk(self, chunk_ref: dict, storage_context: dict) -> bytes:
        """Download chunk from Telegram"""
        # Implement download logic
        return b"encrypted_chunk_data"
```

**Step 2:** Register in `providers/__init__.py`

```python
from .telegram.telegram_provider import TelegramStorageProvider

PLATFORM_TELEGRAM = "Telegram"

PLATFORM_CHOICES = [
    # ... existing choices
    (PLATFORM_TELEGRAM, "Telegram"),
]

PROVIDER_REGISTRY = {
    # ... existing providers
    PLATFORM_TELEGRAM: TelegramStorageProvider,
}
```

---

## Development

### Project Structure

```
discloud/
├── apps/
│   ├── files/                      # File management app
│   │   ├── services/               # Business logic
│   │   │   ├── file_service.py     # File upload/download orchestration
│   │   │   ├── encryption_service.py  # AES-256-CBC encryption
│   │   │   └── storage_service.py  # Storage provider abstraction
│   │   ├── models.py               # File and Chunk models
│   │   ├── repository.py           # Data access layer
│   │   ├── views.py                # Web views
│   │   └── tests/                  # Test suite
│   │
│   └── storage_providers/          # Storage provider system
│       ├── providers/              # Provider implementations
│       │   ├── base.py             # Abstract base class
│       │   ├── discord/            # Discord provider
│       │   └── .../                # Other provider implementations
│       ├── models.py               # StorageProvider model
│       ├── repository.py           # Provider data access
│       └── tests/                  # Provider tests
│
├── discloud/                       # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
│
├── templates/                      # HTML templates
│   ├── upload.html
│   ├── file_list.html
│   └── file_detail.html
│
├── manage.py                       # Django management script
├── pytest.ini                      # Pytest configuration
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

### Key Patterns

#### 1. **Encryption with Prepended IV**

```python
# Each chunk: [16-byte IV][ciphertext]
iv = os.urandom(16)
cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
ciphertext = cipher.encryptor().update(data) + cipher.encryptor().finalize()
return iv + ciphertext  # IV prepended for independent decryption
```

#### 2. **Streaming Decryption**

```python
def get_decrypted_stream(self, file: File):
    """Generator yields decrypted chunks without loading entire file"""
    for chunk in file.chunks.all().order_by('chunk_order'):
        encrypted_data = self.storage_service.download_chunk(chunk.chunk_ref)
        decrypted = self.encryption_service.decrypt_chunk(encrypted_data)
        yield decrypted
```

#### 3. **Repository Pattern**

```python
# Abstract interface
class BaseFileRepository(ABC):
    @abstractmethod
    def create_file(self, **kwargs) -> File:
        pass

# Django implementation
class FileRepositoryDjango(BaseFileRepository):
    def create_file(self, **kwargs) -> File:
        return File.objects.create(**kwargs)
```

---

### Running Tests

```powershell
# Run all tests
pytest

# Run specific test file
pytest apps/files/tests/test_file_service.py

# Run with coverage
pytest --cov=apps --cov-report=html

# Skip real API tests (requires Discord credentials)
pytest -m "not real_api"

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration
```

### Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Pure logic tests, no database
- `@pytest.mark.integration` - Cross-component tests with DB
- `@pytest.mark.django_db` - Tests requiring database access
- `@pytest.mark.real_api` - Tests making actual external API calls

### Test Structure

```python
# Example test with mocking
@pytest.mark.django_db
def test_upload_file(mock_storage_service, sample_file):
    """Test file upload with mocked storage"""
    file_service = FileService(
        storage_service=mock_storage_service
    )
    
    result = file_service.upload_file(
        file_stream=sample_file,
        original_filename='test.txt'
    )
    
    assert result.original_filename == 'test.txt'
    assert result.chunks.count() > 0
```

### Fixtures

Common fixtures in `conftest.py`:

- `discord_provider` - Discord provider instance
- `sample_file` - Test file data
- `mock_storage_service` - Mocked storage service
- `mock_encryption_service` - Mocked encryption service

---

## API Reference

### FileService

Main service for file operations.

```python
class FileService:
    def upload_file(
        self,
        file_stream: BinaryIO,
        original_filename: str,
        description: str = "",
        chunk_size: int = None
    ) -> File:
        """
        Upload and encrypt a file.
        
        Args:
            file_stream: File-like object to upload
            original_filename: Original name of the file
            description: Optional file description
            chunk_size: Chunk size in bytes (default: provider max)
        
        Returns:
            File instance with encrypted chunks stored
        """
    
    def get_decrypted_stream(self, file: File) -> Generator[bytes, None, None]:
        """
        Stream decrypted file chunks.
        
        Args:
            file: File instance to download
        
        Yields:
            Decrypted chunk bytes
        """
    
    def delete_file(self, file: File) -> None:
        """Delete file and all its chunks from storage and database"""
```

### EncryptionService

Handles AES-256-CBC encryption.

```python
class EncryptionService:
    def __init__(self, key: bytes = None):
        """Initialize with 32-byte AES key (auto-generated if None)"""
    
    def encrypt_chunk(self, data: bytes) -> bytes:
        """
        Encrypt data with AES-256-CBC.
        Returns: [16-byte IV][ciphertext]
        """
    
    def decrypt_chunk(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data. Expects format: [16-byte IV][ciphertext]
        """
```

### StorageService

Abstracts storage provider interactions.

```python
class StorageService:
    def __init__(self, storage_provider_name: str = 'discord_default'):
        """Initialize with provider from database"""
    
    def prepare_storage(self, file_metadata: dict) -> dict:
        """Create storage container (e.g., Discord thread)"""
    
    def upload_chunk(self, chunk_data: bytes, storage_context: dict) -> dict:
        """Upload chunk, returns provider-specific metadata"""
    
    def download_chunk(self, chunk_ref: dict, storage_context: dict) -> bytes:
        """Download chunk using provider metadata"""
    
    def get_max_chunk_size(self) -> int:
        """Get maximum chunk size for current provider"""
```

---

## Security

### Encryption Details

- **Algorithm**: AES-256-CBC (Advanced Encryption Standard)
- **Key Size**: 256 bits (32 bytes)
- **IV**: Unique 128-bit (16 bytes) initialization vector per chunk
- **Padding**: PKCS7 padding to align to 16-byte blocks
- **Key Storage**: Per-file encryption keys stored in database as `BinaryField`

---

## Contributing

Contributions are welcome! Please follow these guidelines:

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-new-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit: `git commit -am 'Add new feature'`
6. Push: `git push origin feature/my-new-feature`
7. Submit a Pull Request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made with ❤️ by Théo Torregrossa**
