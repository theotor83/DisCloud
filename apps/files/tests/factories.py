"""
Factory classes for generating test data.

Using factory_boy to create model instances for testing.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from apps.files.models import File, Chunk
from apps.storage_providers.models import StorageProvider

fake = Faker()


class StorageProviderFactory(DjangoModelFactory):
    """Factory for creating StorageProvider instances."""
    
    class Meta:
        model = StorageProvider
    
    name = factory.Sequence(lambda n: f'test_provider_{n}')
    platform = 'Discord'
    is_active = True
    config = factory.LazyFunction(lambda: {
        'bot_token': fake.uuid4(),
        'server_id': fake.numerify(text='##################'),
        'channel_id': fake.numerify(text='##################')
    })


class FileFactory(DjangoModelFactory):
    """Factory for creating File instances."""
    
    class Meta:
        model = File
    
    original_filename = factory.Faker('file_name')
    encrypted_filename = factory.LazyFunction(lambda: f'{fake.uuid4()}.enc')
    description = factory.Faker('sentence')
    encryption_key = factory.LazyFunction(lambda: b'0' * 32)
    storage_provider = factory.SubFactory(StorageProviderFactory)
    storage_metadata = factory.LazyFunction(lambda: {
        'thread_id': fake.numerify(text='##################')
    })


class ChunkFactory(DjangoModelFactory):
    """Factory for creating Chunk instances."""
    
    class Meta:
        model = Chunk
    
    file = factory.SubFactory(FileFactory)
    chunk_order = factory.Sequence(lambda n: n)
    provider_chunk_id = factory.LazyFunction(lambda: {
        'message_id': fake.numerify(text='##################'),
        'attachment_id': fake.numerify(text='##################')
    })


# Example usage in tests:
"""
import pytest
from apps.files.tests.factories import FileFactory, ChunkFactory

@pytest.mark.django_db
def test_using_factories():
    # Create a file with default values
    file = FileFactory()
    
    # Create a file with custom values
    file = FileFactory(original_filename='custom.pdf')
    
    # Create a file with 5 chunks
    file = FileFactory()
    chunks = ChunkFactory.create_batch(5, file=file)
    
    # Create multiple files
    files = FileFactory.create_batch(10)
"""
