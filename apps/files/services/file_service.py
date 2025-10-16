from apps.files.models import File, Chunk
from services.encryption_service import EncryptionService
from services.storage_service import StorageService

class FileService:
    """
    Orchestrates file upload, download, and deletion by coordinating encryption,
    storage, and database operations. Primary service layer for file management.
    """

    def __init__(self, file_repository, storage_service=None, encryption_service=None):
        self.file_repository = file_repository
        if not storage_service:
            print("No StorageService provided, using default.")
            storage_service = StorageService(provider_name='discord_default')  # Use the default provider
        self._storage_service = storage_service
        if not encryption_service:
            encryption_service = EncryptionService()
        self._encryption_service = encryption_service

    def get_decrypted_stream(self, file_instance: File):
        """
        Orchestrates: fetch chunks -> download from storage -> decrypt -> yield
        """
        if not self._storage_service:
            raise ValueError("StorageService is not configured")
        if not self._encryption_service:
            raise ValueError("EncryptionService is not configured")

        chunks = self.file_repository.list_chunks(file_instance).order_by('chunk_order')
        if not chunks.exists():
            raise ValueError("No chunks found for the given file")

        for chunk in chunks:
            encrypted_data = self._storage_service.download_chunk(
                chunk.provider_chunk_id,
                file_metadata={
                    'original_filename': file_instance.original_filename,
                    'file_id': str(file_instance.id),
                    'chunk_order': chunk.chunk_order,
                }
            )
            decrypted_data = self._encryption_service.decrypt_chunk(
                encrypted_data,
                file_instance.encryption_key
            )
            yield decrypted_data

    def upload_file(self, file_stream, filename, storage_provider_name, chunk_size):
        """Orchestrates: chunk reading -> encrypt -> store -> save DB records"""
        pass

    def delete_file(self, file_instance: File):
        """Orchestrates: delete chunks from storage -> delete DB records"""
        pass