"""
Unit tests for File and Chunk models.
"""
import pytest
from django.db import IntegrityError
from django.utils import timezone
from apps.files.models import File, Chunk
from apps.storage_providers.models import StorageProvider


@pytest.mark.django_db
class TestFileModel:
    """Test cases for the File model."""

    def test_create_file(self, discord_provider, sample_encryption_key):
        """Test creating a File object with required fields."""
        file_obj = File.objects.create(
            original_filename='document.pdf',
            encrypted_filename='abc123.enc',
            description='Test document',
            encryption_key=sample_encryption_key,
            storage_provider=discord_provider,
            storage_metadata={'thread_id': '123456'}
        )
        
        assert file_obj.id is not None
        assert file_obj.original_filename == 'document.pdf'
        assert file_obj.encrypted_filename == 'abc123.enc'
        assert file_obj.encryption_key == sample_encryption_key
        assert file_obj.storage_provider == discord_provider
        assert file_obj.uploaded_at is not None
        assert isinstance(file_obj.uploaded_at, timezone.datetime)

    def test_file_str_representation(self, sample_file):
        """Test the string representation of a File object."""
        str_repr = str(sample_file)
        assert 'test_document.pdf' in str_repr
        assert sample_file.uploaded_at.strftime('%Y-%m-%d %H:%M') in str_repr

    def test_encrypted_filename_unique_constraint(self, discord_provider, sample_encryption_key):
        """Test that encrypted_filename must be unique."""
        File.objects.create(
            original_filename='file1.txt',
            encrypted_filename='unique123.enc',
            encryption_key=sample_encryption_key,
            storage_provider=discord_provider
        )
        
        # Attempting to create another file with the same encrypted_filename should fail
        with pytest.raises(IntegrityError):
            File.objects.create(
                original_filename='file2.txt',
                encrypted_filename='unique123.enc',  # Same encrypted name
                encryption_key=sample_encryption_key,
                storage_provider=discord_provider
            )

    def test_file_ordering(self, discord_provider, sample_encryption_key):
        """Test that files are ordered by uploaded_at descending."""
        file1 = File.objects.create(
            original_filename='first.txt',
            encrypted_filename='first.enc',
            encryption_key=sample_encryption_key,
            storage_provider=discord_provider
        )
        
        file2 = File.objects.create(
            original_filename='second.txt',
            encrypted_filename='second.enc',
            encryption_key=sample_encryption_key,
            storage_provider=discord_provider
        )
        
        files = list(File.objects.all())
        # Most recent first (file2 created after file1)
        assert files[0].id == file2.id
        assert files[1].id == file1.id

    def test_file_cascade_delete(self, sample_file):
        """Test that deleting a file cascades to its chunks."""
        # Create chunks for the file
        Chunk.objects.create(
            file=sample_file,
            chunk_order=0,
            provider_chunk_metadata={'message_id': '111'}
        )
        Chunk.objects.create(
            file=sample_file,
            chunk_order=1,
            provider_chunk_metadata={'message_id': '222'}
        )
        
        assert sample_file.chunks.count() == 2
        
        # Delete the file
        file_id = sample_file.id
        sample_file.delete()
        
        # Verify chunks are deleted
        assert Chunk.objects.filter(file_id=file_id).count() == 0

    def test_storage_metadata_json_field(self, sample_file):
        """Test that storage_metadata can store and retrieve JSON data."""
        sample_file.storage_metadata = {
            'thread_id': '999888777',
            'channel_name': 'test-channel',
            'extra_info': {'nested': 'value'}
        }
        sample_file.save()
        
        # Reload from database
        reloaded = File.objects.get(id=sample_file.id)
        assert reloaded.storage_metadata['thread_id'] == '999888777'
        assert reloaded.storage_metadata['extra_info']['nested'] == 'value'


@pytest.mark.django_db
class TestChunkModel:
    """Test cases for the Chunk model."""

    def test_create_chunk(self, sample_file):
        """Test creating a Chunk object."""
        chunk = Chunk.objects.create(
            file=sample_file,
            chunk_order=0,
            provider_chunk_metadata={'message_id': 'msg123', 'attachment_id': 'att456'}
        )
        
        assert chunk.id is not None
        assert chunk.file == sample_file
        assert chunk.chunk_order == 0
        assert chunk.provider_chunk_metadata['message_id'] == 'msg123'

    def test_chunk_str_representation(self, sample_file):
        """Test the string representation of a Chunk object."""
        chunk = Chunk.objects.create(
            file=sample_file,
            chunk_order=2,
            provider_chunk_metadata={'message_id': 'test'}
        )
        
        str_repr = str(chunk)
        assert 'Chunk 2' in str_repr
        assert 'test_document.pdf' in str_repr

    def test_chunk_ordering(self, sample_file):
        """Test that chunks are ordered by file and chunk_order."""
        chunk2 = Chunk.objects.create(
            file=sample_file,
            chunk_order=2,
            provider_chunk_metadata={'message_id': 'msg2'}
        )
        chunk0 = Chunk.objects.create(
            file=sample_file,
            chunk_order=0,
            provider_chunk_metadata={'message_id': 'msg0'}
        )
        chunk1 = Chunk.objects.create(
            file=sample_file,
            chunk_order=1,
            provider_chunk_metadata={'message_id': 'msg1'}
        )
        
        chunks = list(sample_file.chunks.all())
        assert chunks[0].chunk_order == 0
        assert chunks[1].chunk_order == 1
        assert chunks[2].chunk_order == 2

    def test_chunk_unique_together_constraint(self, sample_file):
        """Test that (file, chunk_order) must be unique together."""
        Chunk.objects.create(
            file=sample_file,
            chunk_order=0,
            provider_chunk_metadata={'message_id': 'msg1'}
        )
        
        # Attempting to create another chunk with same file and chunk_order should fail
        with pytest.raises(IntegrityError):
            Chunk.objects.create(
                file=sample_file,
                chunk_order=0,  # Same order
                provider_chunk_metadata={'message_id': 'msg2'}
            )

    def test_chunk_related_name(self, sample_file):
        """Test accessing chunks through the file's related name."""
        Chunk.objects.create(
            file=sample_file,
            chunk_order=0,
            provider_chunk_metadata={'message_id': 'msg1'}
        )
        Chunk.objects.create(
            file=sample_file,
            chunk_order=1,
            provider_chunk_metadata={'message_id': 'msg2'}
        )
        
        # Access via related name
        assert sample_file.chunks.count() == 2
        assert sample_file.chunks.filter(chunk_order=0).exists()

    def test_provider_chunk_metadata_json_storage(self, sample_file):
        """Test that provider_chunk_metadata can store complex JSON data."""
        chunk = Chunk.objects.create(
            file=sample_file,
            chunk_order=0,
            provider_chunk_metadata={
                'message_id': '123456789',
                'attachment_id': '987654321',
                'channel_id': '111222333',
                'metadata': {'size': 1024, 'hash': 'abc123'}
            }
        )
        
        # Reload from database
        reloaded = Chunk.objects.get(id=chunk.id)
        assert reloaded.provider_chunk_metadata['message_id'] == '123456789'
        assert reloaded.provider_chunk_metadata['metadata']['size'] == 1024


@pytest.mark.django_db
class TestFileChunkRelationship:
    """Test the relationship between File and Chunk models."""

    def test_file_multiple_chunks(self, sample_file):
        """Test a file can have multiple chunks."""
        for i in range(5):
            Chunk.objects.create(
                file=sample_file,
                chunk_order=i,
                provider_chunk_metadata={'message_id': f'msg{i}'}
            )
        
        assert sample_file.chunks.count() == 5

    def test_chunks_filtered_by_file(self, discord_provider, sample_encryption_key):
        """Test that chunks are properly filtered by file."""
        file1 = File.objects.create(
            original_filename='file1.txt',
            encrypted_filename='file1.enc',
            encryption_key=sample_encryption_key,
            storage_provider=discord_provider
        )
        file2 = File.objects.create(
            original_filename='file2.txt',
            encrypted_filename='file2.enc',
            encryption_key=sample_encryption_key,
            storage_provider=discord_provider
        )
        
        # Create chunks for file1
        Chunk.objects.create(file=file1, chunk_order=0, provider_chunk_metadata={'msg': '1'})
        Chunk.objects.create(file=file1, chunk_order=1, provider_chunk_metadata={'msg': '2'})
        
        # Create chunks for file2
        Chunk.objects.create(file=file2, chunk_order=0, provider_chunk_metadata={'msg': '3'})
        
        assert file1.chunks.count() == 2
        assert file2.chunks.count() == 1
        assert Chunk.objects.count() == 3
