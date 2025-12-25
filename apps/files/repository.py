from abc import ABC, abstractmethod
from .models import File, Chunk


class BaseFileRepository(ABC):
    """
    Abstract base class for file repository implementations.
    Defines the contract for managing File and Chunk objects.
    """

    @abstractmethod
    def create_file(self, original_filename, encrypted_filename, description, encryption_key, storage_provider, storage_context, client_signature=None):
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
    def get_files_with_signature(self, client_signature):
        """
        Retrieves all File objects with the given client signature.
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
    def change_file_status(self, file_id, new_status):
        """
        Updates the status field of a File object.
        """
        pass

    @abstractmethod
    def find_pending_file(self, client_signature):
        """
        Finds a File object with the given client signature that is in 'PENDING' status.
        Returns None if no such file exists.
        If multiple files match, returns the one with the biggest number of chunks.
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

    @abstractmethod
    def get_chunk_orders(self, file_instance):
        """
        Returns a list of chunk orders (integers) for the given File.
        """
        pass





class FileRepositoryDjango(BaseFileRepository):
    """
    Django ORM implementation of the BaseFileRepository.
    Encapsulates all database interactions related to files and their chunks.
    """

    def create_file(self, original_filename, encrypted_filename, description, encryption_key, storage_provider, storage_context, client_signature=None):
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
            client_signature=client_signature,
            status='PENDING'
        )
        return file_instance

    def get_file(self, file_id):
        """
        Retrieves a File object by its ID.
        """
        return File.objects.get(pk=file_id)

    def get_files_with_signature(self, client_signature):
        """
        Retrieves all File objects with the given client signature.
        """
        return File.objects.filter(client_signature=client_signature)

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

    def change_file_status(self, file_id, new_status):
        """
        Updates the status field of a File object.
        Will raise an error if the new_status is not a valid choice.
        """
        if new_status not in ['PENDING', 'COMPLETED', 'FAILED', 'ERROR']:
            raise ValueError(f"Invalid status: {new_status}")
        File.objects.filter(pk=file_id).update(status=new_status)

    def find_pending_file(self, client_signature):
        """
        Finds a File object with the given client signature that is in 'PENDING' status.
        Returns None if no such file exists.
        If multiple files match, returns the one with the biggest number of chunks.
        """
        try:
            files = File.objects.filter(client_signature=client_signature, status='PENDING')
            if not files.exists():
                return None
            
            if files.count() == 1:
                return files.first()
            
            # If multiple, return the one with the most chunks
            max_chunk_count = -1
            selected_file = None

            for file in files:
                chunk_count = self.list_chunks(file).count()
                if chunk_count > max_chunk_count:
                    max_chunk_count = chunk_count
                    selected_file = file

            return selected_file
        
        except File.DoesNotExist:
            return None

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
    
    def get_chunk_orders(self, file_instance):
        """
        Returns a list of chunk orders (integers) for the given File.
        """
        return list(file_instance.chunks.values_list('chunk_order', flat=True))