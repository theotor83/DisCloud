from .models import File, Chunk

class FileRepository:
    """
    Repository class for managing File and Chunk objects.
    Encapsulates all database interactions related to files and their chunks.
    """

    @staticmethod
    def create_file(original_filename, encrypted_filename, description, encryption_key, storage_provider, storage_metadata):
        """
        Creates and returns a new File object.
        """
        file_instance = File.objects.create(
            original_filename=original_filename,
            encrypted_filename=encrypted_filename,
            description=description,
            encryption_key=encryption_key,
            storage_provider=storage_provider,
            storage_metadata=storage_metadata
        )
        return file_instance

    @staticmethod
    def get_file(file_id):
        """
        Retrieves a File object by its ID.
        """
        return File.objects.get(pk=file_id)

    @staticmethod
    def list_files():
        """
        Returns a queryset of all File objects.
        """
        return File.objects.all()

    @staticmethod
    def update_file(file_id, **kwargs):
        """
        Updates fields of a File object.
        Accepts keyword arguments for fields to be updated.
        """
        File.objects.filter(pk=file_id).update(**kwargs)

    @staticmethod
    def delete_file(file_id):
        """
        Deletes a File object by its ID.
        """
        File.objects.filter(pk=file_id).delete()

    @staticmethod
    def create_chunk(file_instance, chunk_order, provider_chunk_id):
        """
        Creates and returns a new Chunk object associated with the given File.
        """
        chunk_instance = Chunk.objects.create(
            file=file_instance,
            chunk_order=chunk_order,
            provider_chunk_id=provider_chunk_id
        )
        return chunk_instance

    @staticmethod
    def list_chunks(file_instance):
        """
        Returns a queryset of all Chunk objects associated with the given File.
        """
        return file_instance.chunks.all()