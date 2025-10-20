from django import forms
from apps.storage_providers.models import StorageProvider


class FileUploadForm(forms.Form):
    """
    Form for uploading files with description and storage provider selection.
    """
    uploaded_file = forms.FileField(
        label="Select file",
        required=True,
        widget=forms.FileInput(attrs={
            'id': 'id_uploaded_file',
            'class': 'file-input'
        })
    )
    
    description = forms.CharField(
        label="Description (optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'id': 'id_description',
            'class': 'description-input',
            'rows': 3,
            'placeholder': 'Add a description for this file...'
        })
    )
    
    storage_provider = forms.ModelChoiceField(
        label="Storage provider",
        queryset=StorageProvider.objects.all(),
        required=True,
        empty_label="Choose a storage provider",
        widget=forms.Select(attrs={
            'id': 'id_storage_provider',
            'class': 'storage-provider-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default provider if only one exists
        provider_count = StorageProvider.objects.count()
        if provider_count == 1:
            self.fields['storage_provider'].initial = StorageProvider.objects.first()
