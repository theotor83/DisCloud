from abc import ABC, abstractmethod
from .models import File, Chunk


class BaseFileRepository(ABC):
    """
    Abstract base class for file repository implementations.
    Defines the contract for managing File and Chunk objects.
    """

    @abstractmethod
    def create_file(self, original_filename, encrypted_filename, description, encryption_key, storage_provider, storage_context, sha256_signature=None):
        """
        Creates and returns a new File object.
        """
        pass

    @abstractmethod
    def get_file(self, file_id):
        """
        Retrieves a File object by its ID.
        """
        pass

    @abstractmethod
    def list_files(self):
        """
        Returns a queryset or list of all File objects.
        """
        pass

    @abstractmethod
    def update_file(self, file_id, **kwargs):
        """
        Updates fields of a File object.
        Accepts keyword arguments for fields to be updated.
        """
        pass

    @abstractmethod
    def delete_file(self, file_id):
        """
        Deletes a File object by its ID.
        """
        pass

    @abstractmethod
    def create_chunk(self, file_instance, chunk_order, chunk_ref):
        """
        Creates and returns a new Chunk object associated with the given File.
        """
        pass

    @abstractmethod
    def list_chunks(self, file_instance):
        """
        Returns a queryset or list of all Chunk objects associated with the given File.
        """
        pass


class FileRepositoryDjango(BaseFileRepository):
    """
    Django ORM implementation of the BaseFileRepository.
    Encapsulates all database interactions related to files and their chunks.
    """

    def create_file(self, original_filename, encrypted_filename, description, encryption_key, storage_provider, storage_context, sha256_signature=None):
        """
        Creates and returns a new File object.
        """
        file_instance = File.objects.create(
            original_filename=original_filename,
            encrypted_filename=encrypted_filename,
            description=description,
            encryption_key=encryption_key,
            storage_provider=storage_provider,
            storage_context=storage_context,
            sha256_signature=sha256_signature
        )
        return file_instance

    def get_file(self, file_id):
        """
        Retrieves a File object by its ID.
        """
        return File.objects.get(pk=file_id)

    def list_files(self):
        """
        Returns a queryset of all File objects.
        """
        return File.objects.all()

    def update_file(self, file_id, **kwargs):
        """
        Updates fields of a File object.
        Accepts keyword arguments for fields to be updated.
        """
        File.objects.filter(pk=file_id).update(**kwargs)

    def delete_file(self, file_id):
        """
        Deletes a File object by its ID.
        """
        File.objects.filter(pk=file_id).delete()

    def create_chunk(self, file_instance, chunk_order, chunk_ref):
        """
        Creates and returns a new Chunk object associated with the given File.
        """
        chunk_instance = Chunk.objects.create(
            file=file_instance,
            chunk_order=chunk_order,
            chunk_ref=chunk_ref
        )
        return chunk_instance

    def list_chunks(self, file_instance):
        """
        Returns a queryset of all Chunk objects associated with the given File.
        """
        return file_instance.chunks.all()