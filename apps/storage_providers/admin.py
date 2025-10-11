from django.contrib import admin
from .models import StorageProvider


@admin.register(StorageProvider)
class StorageProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'file_count']
    list_filter = ['platform']
    search_fields = ['name']
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('name', 'platform')
        }),
        ('Configuration', {
            'fields': ('config',),
            'description': 'JSON configuration for this storage provider'
        }),
    )
    
    def file_count(self, obj):
        return obj.file_set.count()
    file_count.short_description = 'Files'
