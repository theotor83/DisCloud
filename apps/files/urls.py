from django.urls import path
from . import views

# This is used to namespace the URLs, e.g., {% url 'files:detail' file.id %}
app_name = 'files'

urlpatterns = [
    # Root URL: Displays the list of all uploaded files
    path('', views.file_list, name='list'),


    # URL for the file upload page
    path('upload/', views.upload_file, name='upload'),

    # URL for choosing storage provider type, when creating a new provider
    path('choose-provider/', views.choose_provider, name='choose_provider'),

    # URL for viewing the details of a specific file
    # e.g., /file/1/
    path('file/<int:file_id>/', views.file_detail, name='detail'),

    # URL to trigger the download of a specific file
    # e.g., /file/1/download/
    path('file/<int:file_id>/download/', views.download_file, name='download'),
]