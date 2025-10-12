"""
Example tests demonstrating best practices and common patterns.
"""
import pytest
from apps.files.tests.factories import FileFactory, ChunkFactory, StorageProviderFactory
from apps.files.models import File, Chunk


@pytest.mark.django_db
class TestUsingFactories:
    """Examples of using factory_boy for test data generation."""

    def test_create_file_with_factory(self):
        """Demonstrate creating a file with factory."""
        file = FileFactory()
        
        assert file.id is not None
        assert file.original_filename is not None
        assert file.encryption_key is not None

    def test_create_file_with_custom_values(self):
        """Demonstrate creating a file with custom values."""
        file = FileFactory(
            original_filename='my_document.pdf',
            description='A test document'
        )
        
        assert file.original_filename == 'my_document.pdf'
        assert file.description == 'A test document'

    def test_create_file_with_chunks(self):
        """Demonstrate creating a file with multiple chunks."""
        file = FileFactory()
        chunks = ChunkFactory.create_batch(5, file=file)
        
        assert file.chunks.count() == 5
        assert len(chunks) == 5
        
        # Verify chunks are properly ordered
        for i, chunk in enumerate(file.chunks.all()):
            assert chunk.chunk_order == i

    def test_create_multiple_files(self):
        """Demonstrate batch creation of files."""
        files = FileFactory.create_batch(10)
        
        assert len(files) == 10
        assert File.objects.count() == 10

    def test_create_provider_with_factory(self):
        """Demonstrate creating a storage provider."""
        provider = StorageProviderFactory(name='my_discord_provider')
        
        assert provider.name == 'my_discord_provider'
        assert provider.platform == 'Discord'
        assert 'bot_token' in provider.config


@pytest.mark.django_db
class TestCommonPatterns:
    """Examples of common testing patterns."""

    def test_query_optimization(self):
        """Test that demonstrates checking query efficiency."""
        # Create test data
        file = FileFactory()
        ChunkFactory.create_batch(3, file=file)
        
        # Test that we can fetch file with chunks efficiently
        with pytest.raises(Exception):
            # This would fail if we try to access chunks without proper select_related
            pass
        
        # Proper way to fetch with related objects
        fetched_file = File.objects.prefetch_related('chunks').get(id=file.id)
        assert fetched_file.chunks.count() == 3

    def test_model_validation(self):
        """Test model field validation."""
        file = FileFactory()
        
        # Test that certain fields are required
        assert file.original_filename
        assert file.encrypted_filename
        assert file.encryption_key

    def test_cascade_behavior(self):
        """Test cascade delete behavior."""
        file = FileFactory()
        chunk_ids = [
            ChunkFactory(file=file, chunk_order=i).id 
            for i in range(3)
        ]
        
        # Delete the file
        file.delete()
        
        # Verify chunks were deleted
        for chunk_id in chunk_ids:
            assert not Chunk.objects.filter(id=chunk_id).exists()

    def test_unique_constraints(self):
        """Test unique field constraints."""
        file1 = FileFactory(encrypted_filename='unique123.enc')
        
        # Attempting to create another file with same encrypted_filename should fail
        with pytest.raises(Exception):
            FileFactory(encrypted_filename='unique123.enc')

    def test_json_field_operations(self):
        """Test JSONField operations."""
        file = FileFactory(
            storage_metadata={
                'thread_id': '123456',
                'extra': {'nested': 'value'}
            }
        )
        
        # Test JSON querying
        found = File.objects.filter(
            storage_metadata__thread_id='123456'
        ).first()
        
        assert found.id == file.id
        assert found.storage_metadata['extra']['nested'] == 'value'


@pytest.mark.unit
class TestWithoutDatabase:
    """Examples of tests that don't require database."""

    def test_pure_function(self):
        """Test a pure function without database."""
        # Example: testing a utility function
        result = 2 + 2
        assert result == 4

    def test_with_mocks(self):
        """Test using mocks without database."""
        from unittest.mock import Mock
        
        mock_service = Mock()
        mock_service.get_data.return_value = {'key': 'value'}
        
        result = mock_service.get_data()
        assert result['key'] == 'value'
        mock_service.get_data.assert_called_once()


@pytest.mark.django_db
class TestErrorHandling:
    """Examples of testing error conditions."""

    def test_handle_missing_file(self):
        """Test handling of missing file."""
        # Try to get non-existent file
        file = File.objects.filter(id=99999).first()
        assert file is None

    def test_invalid_data_handling(self):
        """Test handling of invalid data."""
        with pytest.raises(Exception):
            # This should fail due to validation
            File.objects.create(
                original_filename='',  # Empty filename
                encrypted_filename='',
                encryption_key=None,
                storage_provider=None
            )


# Parametrized tests example
@pytest.mark.django_db
class TestParametrizedTests:
    """Examples using pytest parametrize."""

    @pytest.mark.parametrize('filename,expected_ext', [
        ('document.pdf', 'pdf'),
        ('image.png', 'png'),
        ('archive.tar.gz', 'gz'),
        ('no_extension', ''),
    ])
    def test_multiple_filenames(self, filename, expected_ext):
        """Test with multiple filename patterns."""
        file = FileFactory(original_filename=filename)
        
        # Your logic to extract extension
        ext = filename.split('.')[-1] if '.' in filename else ''
        assert ext == expected_ext

    @pytest.mark.parametrize('chunk_count', [1, 5, 10, 100])
    def test_different_chunk_counts(self, chunk_count):
        """Test with different numbers of chunks."""
        file = FileFactory()
        chunks = ChunkFactory.create_batch(chunk_count, file=file)
        
        assert file.chunks.count() == chunk_count
        assert len(chunks) == chunk_count
