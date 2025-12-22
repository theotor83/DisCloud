from django.db import models

class File(models.Model):
    """
    Represents a file uploaded by the user.
    The actual file content is not stored in the database.
    """
    original_filename = models.CharField(max_length=255)
    encrypted_filename = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    encryption_key = models.BinaryField() # Store the unique encryption key for this file
    sha256_signature = models.CharField(max_length=64, blank=True, null=True) # Maybe unique=True ? For now, will allow duplicates, and will also be used to see if file upload was incomplete
    uploaded_at = models.DateTimeField(auto_now_add=True)
    storage_provider = models.ForeignKey('storage_providers.StorageProvider', on_delete=models.PROTECT)
    storage_context = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, default='PENDING') # e.g., 'PENDING', 'COMPLETED', 'FAILED', 'ERROR'

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename} ({self.uploaded_at.strftime('%Y-%m-%d %H:%M')})"


class Chunk(models.Model):
    """
    Represents a chunk of a larger file.
    This is necessary for services with file size limits.
    """
    file = models.ForeignKey(File, related_name='chunks', on_delete=models.CASCADE)
    chunk_order = models.IntegerField()
    # Store provider-specific details needed to retrieve the chunk
    chunk_ref = models.JSONField() # e.g., Discord message ID for this chunk

    class Meta:
        verbose_name = "Chunk"
        verbose_name_plural = "Chunks"
        ordering = ['file', 'chunk_order']
        unique_together = [['file', 'chunk_order']]

    def __str__(self):
        return f"Chunk {self.chunk_order} of {self.file.original_filename}"