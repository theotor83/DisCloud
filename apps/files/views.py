import logging
from django.shortcuts import render
from django.http import StreamingHttpResponse
from .models import File
from .repository import FileRepositoryDjango
from .services.file_service import FileService
from .services.storage_service import StorageService
from .services.encryption_service import EncryptionService
from apps.storage_providers.repository import StorageProviderRepositoryDjango

logger = logging.getLogger(__name__)

def upload_file(request):
    """
    Handles the file upload process.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('uploaded_file')
        if not uploaded_file:
            logger.error("No file uploaded in the request.")
            return render(request, 'upload.html', {'error': 'No file uploaded.'})
        
        logger.info(f"Starting upload for file: {uploaded_file.name}")
        storage_service = StorageService('discord_default')

        logger.info("Initializing FileService for upload...")
        file_service = FileService(
            file_repository=FileRepositoryDjango(),
            storage_service=storage_service,
            encryption_service=EncryptionService()
        )
        logger.info("Initialized FileService.")

        
        try:
            result = file_service.upload_file(
                file_stream=uploaded_file,
                filename=uploaded_file.name,
                storage_provider_name="discord_default", # Placeholder
                chunk_size=storage_service.get_max_chunk_size(),
                storage_provider_repository=StorageProviderRepositoryDjango()
            )
            logger.info(f"File uploaded successfully! File ID: {result.id}")
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            pass

    return render(request, 'upload.html')

def file_list(request):
    """
    Displays a list of all uploaded files.
    """
    file_repository = FileRepositoryDjango()
    files = file_repository.list_files()
    return render(request, 'file_list.html', {'files': files})

def file_detail(request, file_id):
    """
    Displays the details of a specific file and allows for editing
    the description and thumbnail.
    """
    # Fetch file details and handle form submission for updates.
    pass

def download_file(request, file_id):
    """
    Handles the file download process.
    Returns a StreamingHttpResponse to send the file to the user
    without loading it all into memory.
    """
    logger.info(f"Starting download for file ID: {file_id}")
    
    file_repository = FileRepositoryDjango()
    
    try:
        file_instance = file_repository.get_file(file_id)
        logger.info(f"Retrieved file: {file_instance.id}")
    except Exception as e:
        logger.error(f"Failed to retrieve file {file_id}: {str(e)}")
        raise
    
    encryption_key = file_instance.encryption_key
    logger.info("Initializing FileService for download...")
    file_service = FileService(file_repository, encryption_service=EncryptionService(encryption_key))
    # In the future, file_service can accept a StorageService parameter based on the file's storage provider.
    
    logger.info(f"Creating streaming response for file: {file_instance.id}")
    response = StreamingHttpResponse(file_service.get_decrypted_stream(file_instance))
    response['Content-Disposition'] = f'attachment; filename="{file_instance.original_filename}"'
    logger.info(f"Download initiated successfully for file: {file_instance.id}")
    return response