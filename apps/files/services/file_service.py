from apps.files.models import File, Chunk
from apps.files.services.encryption_service import EncryptionService
from apps.files.services.storage_service import StorageService
from django.core.files.uploadedfile import UploadedFile
from apps.storage_providers.repository import BaseStorageProviderRepository
from apps.files.repository import BaseFileRepository

class FileService:
    """
    Orchestrates file upload, download, and deletion by coordinating encryption,
    storage, and database operations. Primary service layer for file management.
    """

    def __init__(self, file_repository: BaseFileRepository, storage_service=None, encryption_service=None):
        self.file_repository = file_repository

        if not storage_service:
            print("No StorageService provided, using default.")
            storage_service = StorageService(provider_name='discord_default')  # Use the default provider for now
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
                chunk.provider_chunk_metadata,
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

    def upload_file(self, file_stream: UploadedFile, filename: str,
                    storage_provider_name: str, chunk_size: int, 
                    storage_provider_repository: BaseStorageProviderRepository) -> File:
        """
        Orchestrates: chunk reading -> encrypt -> store -> save DB records
        """
        encryption_key = self._encryption_service.key
        
        # Prepare for the new File object in database
        file_metadata = {"filename":filename}
        storage_metadata = self._storage_service.prepare_storage(file_metadata)

        # Creation of the new File object
        file_instance = self.file_repository.create_file(
            filename,
            filename, # Placeholder
            "No description", # Placeholder
            encryption_key,
            self._storage_service.provider,
            storage_metadata,
        )

        chunk_number = 1

        for streamed_chunk in file_stream.chunks(chunk_size=chunk_size):
            encrypted_chunk = self._encryption_service.encrypt_chunk(
                streamed_chunk,
            )

            upload_result = self._storage_service.upload_chunk(encrypted_chunk, storage_metadata)

            self.file_repository.create_chunk(
                file_instance,
                chunk_number,
                upload_result
            )

            chunk_number += 1

        return file_instance

    def delete_file(self, file_instance: File):
        """Orchestrates: delete chunks from storage -> delete DB records"""
        pass