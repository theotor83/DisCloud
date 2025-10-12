class StorageServiceError(Exception):
    """Base exception for storage service errors"""
    pass

class StorageUploadError(StorageServiceError):
    """Raised when chunk upload fails"""
    pass

class StorageDownloadError(StorageServiceError):
    """Raised when chunk download fails"""
    pass