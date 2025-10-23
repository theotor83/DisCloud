import logging
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from django.contrib import messages
from .models import File
from .repository import FileRepositoryDjango
from .services.file_service import FileService
from .services.storage_service import StorageService
from .services.encryption_service import EncryptionService
from apps.storage_providers.repository import StorageProviderRepositoryDjango
from .forms import FileUploadForm

logger = logging.getLogger(__name__)

def upload_file(request):
    """
    Handles the file upload process.
    """
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            uploaded_file = form.cleaned_data['uploaded_file']
            description = form.cleaned_data['description']
            storage_provider = form.cleaned_data['storage_provider']
            
            logger.info(f"Starting upload for file: {uploaded_file.name} using storage provider: {storage_provider.name}")
            
            storage_service = StorageService(storage_provider.name)

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
                    storage_provider_name=storage_provider.name,
                    chunk_size=storage_service.get_max_chunk_size(),
                    storage_provider_repository=StorageProviderRepositoryDjango(),
                    description=description
                )
                logger.info(f"File uploaded successfully! File ID: {result.id}")
                messages.success(request, f'File "{uploaded_file.name}" uploaded successfully!')
                return redirect('files:list')
            except Exception as e:
                logger.error(f"File upload failed: {str(e)}")
                messages.error(request, f'File upload failed: {str(e)}')
        else:
            logger.error(f"Form validation failed: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FileUploadForm()

    return render(request, 'upload.html', {'form': form})

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
    file_service = FileService(
        file_repository,
        storage_service=StorageService(file_instance.storage_provider.name), # Dynamically create based on file's provider
        encryption_service=EncryptionService(encryption_key)
        )

    
    logger.info(f"Creating streaming response for file: {file_instance.id}")
    response = StreamingHttpResponse(file_service.get_decrypted_stream(file_instance))
    response['Content-Disposition'] = f'attachment; filename="{file_instance.original_filename}"'
    logger.info(f"Download initiated successfully for file: {file_instance.id}")
    return response