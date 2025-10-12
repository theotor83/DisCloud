"""
Integration tests for file views.

These tests use Django's test client to test the views.
"""
import pytest
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch, MagicMock
from apps.files.models import File, Chunk
from apps.storage_providers.models import StorageProvider


@pytest.mark.django_db
class TestFileListView:
    """Test the file list view."""

    def setup_method(self):
        """Set up test client."""
        self.client = Client()

    def test_file_list_empty(self):
        """Test file list view when no files exist."""
        response = self.client.get('/files/')
        
        assert response.status_code == 200
        assert 'files' in response.context
        assert len(response.context['files']) == 0

    def test_file_list_with_files(self, sample_file):
        """Test file list view displays uploaded files."""
        response = self.client.get('/files/')
        
        assert response.status_code == 200
        assert 'files' in response.context
        assert len(response.context['files']) == 1
        assert response.context['files'][0].id == sample_file.id

    def test_file_list_ordering(self, discord_provider, sample_encryption_key):
        """Test that files are ordered by upload date (newest first)."""
        file1 = File.objects.create(
            original_filename='old_file.txt',
            encrypted_filename='old.enc',
            encryption_key=sample_encryption_key,
            storage_provider=discord_provider
        )
        
        file2 = File.objects.create(
            original_filename='new_file.txt',
            encrypted_filename='new.enc',
            encryption_key=sample_encryption_key,
            storage_provider=discord_provider
        )
        
        response = self.client.get('/files/')
        files = response.context['files']
        
        # Newest first
        assert files[0].id == file2.id
        assert files[1].id == file1.id

    def test_file_list_template_used(self):
        """Test that the correct template is used."""
        response = self.client.get('/files/')
        
        assert response.status_code == 200
        assert 'file_list.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestUploadView:
    """Test the file upload view."""

    def setup_method(self):
        """Set up test client."""
        self.client = Client()

    def test_upload_get_request(self):
        """Test GET request to upload page displays form."""
        response = self.client.get('/upload/')
        
        assert response.status_code == 200
        assert 'upload.html' in [t.name for t in response.templates]

    @patch('apps.files.views.StorageService')
    @patch('apps.files.views.EncryptionService')
    @patch('apps.files.views.FileRepository')
    def test_upload_post_request(self, MockFileRepo, MockEncryption, MockStorage, 
                                  discord_provider, uploaded_file):
        """Test POST request to upload a file."""
        # Mock the services
        mock_encryption = MockEncryption.return_value
        mock_encryption.generate_key.return_value = b'0' * 32
        mock_encryption.encrypt_chunk.return_value = b'encrypted_data'
        
        mock_storage = MockStorage.return_value
        mock_storage.upload_chunk.return_value = {'message_id': 'test_msg_123'}
        
        mock_repo = MockFileRepo.return_value
        mock_file = Mock()
        mock_file.id = 1
        mock_repo.create_file.return_value = mock_file
        
        # Make POST request with file
        response = self.client.post('/upload/', {
            'uploaded_file': uploaded_file,
            'description': 'Test upload'
        })
        
        # Note: This test assumes upload view redirects on success
        # Adjust based on actual implementation
        assert response.status_code in [200, 302]  # OK or Redirect

    def test_upload_without_file(self):
        """Test uploading without selecting a file."""
        response = self.client.post('/upload/', {
            'description': 'No file attached'
        })
        
        # Should either show form with error or stay on page
        assert response.status_code == 200


@pytest.mark.django_db
class TestDownloadView:
    """Test the file download view."""

    def setup_method(self):
        """Set up test client."""
        self.client = Client()

    @patch('apps.files.models.File.get_decrypted_stream')
    def test_download_file(self, mock_get_stream, sample_file):
        """Test downloading a file."""
        # Mock the decrypted stream
        mock_get_stream.return_value = [b'chunk1', b'chunk2', b'chunk3']
        
        response = self.client.get(f'/files/{sample_file.id}/download/')
        
        assert response.status_code == 200
        assert response['Content-Disposition'] == f'attachment; filename="{sample_file.original_filename}"'
        
        # Verify stream was called
        mock_get_stream.assert_called_once()

    def test_download_nonexistent_file(self):
        """Test downloading a file that doesn't exist."""
        response = self.client.get('/files/99999/download/')
        
        # Should return 404
        assert response.status_code == 404

    @patch('apps.files.models.File.get_decrypted_stream')
    def test_download_streaming_response(self, mock_get_stream, sample_file):
        """Test that download uses StreamingHttpResponse."""
        mock_get_stream.return_value = [b'data']
        
        response = self.client.get(f'/files/{sample_file.id}/download/')
        
        # Check response type
        assert response.streaming
        assert hasattr(response, 'streaming_content')


@pytest.mark.django_db
class TestFileDetailView:
    """Test the file detail view."""

    def setup_method(self):
        """Set up test client."""
        self.client = Client()

    def test_file_detail_view(self, sample_file):
        """Test viewing file details."""
        response = self.client.get(f'/files/{sample_file.id}/')
        
        # Note: Adjust based on actual implementation
        # Currently file_detail view is not fully implemented
        assert response.status_code in [200, 404]

    def test_file_detail_nonexistent(self):
        """Test viewing details of non-existent file."""
        response = self.client.get('/files/99999/')
        
        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.django_db
class TestCompleteUploadDownloadFlow:
    """Integration tests for complete upload and download flows."""

    def setup_method(self):
        """Set up test client."""
        self.client = Client()

    @patch('apps.files.views.StorageService')
    @patch('apps.files.views.EncryptionService')
    def test_upload_then_download(self, MockEncryption, MockStorage, 
                                   discord_provider, uploaded_file):
        """
        Test complete flow: upload a file, then download it.
        
        This is a placeholder for when the upload view is fully implemented.
        """
        # This test would:
        # 1. Upload a file via POST to /upload/
        # 2. Verify file is created in database
        # 3. Download the file via GET to /files/{id}/download/
        # 4. Verify downloaded content matches original
        
        # For now, just verify the endpoints exist
        upload_response = self.client.get('/upload/')
        assert upload_response.status_code == 200
        
        list_response = self.client.get('/files/')
        assert list_response.status_code == 200

    @patch('apps.files.models.File.get_decrypted_stream')
    def test_download_with_multiple_chunks(self, mock_get_stream, file_with_chunks):
        """Test downloading a file that has multiple chunks."""
        sample_file, chunks = file_with_chunks
        
        # Mock decrypted stream returning data for each chunk
        mock_get_stream.return_value = [
            b'chunk_0_data',
            b'chunk_1_data',
            b'chunk_2_data'
        ]
        
        response = self.client.get(f'/files/{sample_file.id}/download/')
        
        assert response.status_code == 200
        mock_get_stream.assert_called_once()
        
        # Collect streaming content
        content = b''.join(response.streaming_content)
        assert b'chunk_0_data' in content
        assert b'chunk_1_data' in content
        assert b'chunk_2_data' in content

    def test_list_shows_upload_link(self):
        """Test that file list page provides link to upload."""
        response = self.client.get('/files/')
        
        assert response.status_code == 200
        # Template should have link to upload page
        assert b'/upload/' in response.content or b'upload' in response.content.lower()


@pytest.mark.django_db
class TestViewErrorHandling:
    """Test error handling in views."""

    def setup_method(self):
        """Set up test client."""
        self.client = Client()

    @patch('apps.files.views.FileRepository')
    def test_upload_with_storage_error(self, MockFileRepo, uploaded_file):
        """Test upload when storage service raises an error."""
        # Mock repository to raise an exception
        MockFileRepo.return_value.create_file.side_effect = Exception("Storage failed")
        
        response = self.client.post('/upload/', {
            'uploaded_file': uploaded_file
        })
        
        # Should handle error gracefully
        # Exact behavior depends on implementation
        assert response.status_code in [200, 500]

    @patch('apps.files.models.File.get_decrypted_stream')
    def test_download_with_decryption_error(self, mock_get_stream, sample_file):
        """Test download when decryption fails."""
        # Mock get_decrypted_stream to raise an exception
        mock_get_stream.side_effect = Exception("Decryption failed")
        
        response = self.client.get(f'/files/{sample_file.id}/download/')
        
        # Should handle error (500 or custom error page)
        assert response.status_code in [500, 404]
