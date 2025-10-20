import logging
from apps.files.models import File
from apps.files.services.encryption_service import EncryptionService
from apps.files.services.storage_service import StorageService
from django.core.files.uploadedfile import UploadedFile
from apps.storage_providers.repository import BaseStorageProviderRepository
from apps.files.repository import BaseFileRepository

logger = logging.getLogger(__name__)

class FileService:
    """
    Orchestrates file upload, download, and deletion by coordinating encryption,
    storage, and database operations. Primary service layer for file management.
    """

    def __init__(self, file_repository: BaseFileRepository, storage_service=None, encryption_service=None):
        if not file_repository:
            raise ValueError("file_repository is required")
        if not isinstance(file_repository, BaseFileRepository):
            raise TypeError("file_repository must be an instance of BaseFileRepository")
        self.file_repository = file_repository
        

        if not storage_service:
            logger.info("No StorageService provided, using default provider 'discord_default'")
            storage_service = StorageService(provider_name='discord_default')  # Use the default provider for now
        self._storage_service = storage_service

        if not encryption_service:
            logger.debug("No EncryptionService provided, creating default instance")
            encryption_service = EncryptionService()
        self._encryption_service = encryption_service
        
        logger.info(f"FileService initialized with provider: {self._storage_service.provider_name if self._storage_service else 'None'}")

    def get_decrypted_stream(self, file_instance: File):
        """
        Orchestrates: fetch chunks -> download from storage -> decrypt -> yield
        """
        logger.info(f"Starting decrypted stream for file: {file_instance.id} ({file_instance.original_filename})")
        
        if not self._storage_service:
            logger.error("StorageService is not configured")
            raise ValueError("StorageService is not configured")
        if not self._encryption_service:
            logger.error("EncryptionService is not configured")
            raise ValueError("EncryptionService is not configured")

        chunks = self.file_repository.list_chunks(file_instance).order_by('chunk_order')
        chunk_count = chunks.count()
        
        if not chunks.exists():
            logger.warning(f"No chunks found for file: {file_instance.original_filename}")
            raise ValueError("No chunks found for the given file")
        
        logger.debug(f"Found {chunk_count} chunks for file: {file_instance.original_filename}")

        for chunk in chunks:
            logger.debug(f"Processing chunk {chunk.chunk_order}/{chunk_count} for file: {file_instance.original_filename}")
            try:
                encrypted_data = self._storage_service.download_chunk(
                    chunk.provider_chunk_metadata,
                    file_metadata=file_instance.storage_metadata
                )
                decrypted_data = self._encryption_service.decrypt_chunk(encrypted_data)
                logger.debug(f"Successfully decrypted chunk {chunk.chunk_order} for file: {file_instance.original_filename}")
                yield decrypted_data
            except Exception as e:
                logger.error(f"Failed to download/decrypt chunk {chunk.chunk_order} for file {file_instance.original_filename}: {str(e)}")
                raise

        logger.info(f"Completed decrypted stream for file: {file_instance.original_filename}")

    def upload_file(self, file_stream: UploadedFile, filename: str,
                    storage_provider_name: str, chunk_size: int, 
                    storage_provider_repository: BaseStorageProviderRepository,
                    description: str = "") -> File:
        """
        Orchestrates: chunk reading -> encrypt -> store -> save DB records
        """
        logger.info(f"Starting file upload: {filename} (chunk_size: {chunk_size} bytes)")
        
        try:
            encryption_key = self._encryption_service.key
            logger.debug(f"Generated encryption key for file: {filename}")
            
            # Prepare for the new File object in database
            file_metadata = {"filename": filename}
            storage_metadata = self._storage_service.prepare_storage(file_metadata)
            logger.debug(f"Prepared storage metadata for file: {filename}")

            storage_provider_model = storage_provider_repository.get_provider_by_name(storage_provider_name)

            # Creation of the new File object
            file_instance = self.file_repository.create_file(
                filename,
                filename, # Placeholder
                description,
                encryption_key,
                storage_provider_model,
                storage_metadata,
            )
            logger.info(f"Created file record in database: {file_instance.id} ({filename})")

            chunk_number = 1

            for streamed_chunk in file_stream.chunks(chunk_size=chunk_size):
                logger.debug(f"Processing chunk {chunk_number} for file: {filename} (size: {len(streamed_chunk)} bytes)")
                
                encrypted_chunk = self._encryption_service.encrypt_chunk(
                    streamed_chunk,
                )
                logger.debug(f"Encrypted chunk {chunk_number} for file: {filename}")

                upload_result = self._storage_service.upload_chunk(encrypted_chunk, storage_metadata)
                logger.debug(f"Uploaded chunk {chunk_number} to storage for file: {filename}")

                self.file_repository.create_chunk(
                    file_instance,
                    chunk_number,
                    upload_result
                )
                logger.debug(f"Created chunk record {chunk_number} in database for file: {file_instance.id}")

                chunk_number += 1

            total_chunks = chunk_number - 1
            logger.info(f"Successfully uploaded file: {file_instance.id} ({filename}) with {total_chunks} chunks")
            return file_instance
            
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {str(e)}", exc_info=True)
            raise

    def delete_file(self, file_instance: File):
        """Orchestrates: delete chunks from storage -> delete DB records"""
        logger.info(f"Starting file deletion: {file_instance.id} ({file_instance.original_filename})")
        # TODO: Implement file deletion logic
        logger.warning(f"File deletion not yet implemented for file: {file_instance.id}")