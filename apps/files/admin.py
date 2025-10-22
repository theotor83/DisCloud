from django.contrib import admin
from .models import File, Chunk


class ChunkInline(admin.TabularInline):
    model = Chunk
    extra = 0
    fields = ['chunk_order', 'chunk_ref']
    readonly_fields = ['chunk_order', 'chunk_ref']


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'storage_provider', 'uploaded_at', 'chunk_count']
    list_filter = ['storage_provider', 'uploaded_at']
    search_fields = ['original_filename', 'description']
    readonly_fields = ['encrypted_filename', 'encryption_key', 'uploaded_at', 'storage_context']
    inlines = [ChunkInline]
    
    fieldsets = (
        ('File Information', {
            'fields': ('original_filename', 'description', 'encrypted_filename')
        }),
        ('Storage Details', {
            'fields': ('storage_provider', 'storage_context')
        }),
        ('Encryption', {
            'fields': ('encryption_key',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('uploaded_at',)
        }),
    )
    
    def chunk_count(self, obj):
        return obj.chunks.count()
    chunk_count.short_description = 'Chunks'


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ['file', 'chunk_order', 'chunk_ref']
    list_filter = ['file__storage_provider']
    search_fields = ['file__original_filename']
    readonly_fields = ['file', 'chunk_order', 'chunk_ref']
