from django.urls import path
from .views import DownloadView

app_name = 'download'
urlpatterns = [
    path('download/<int:target_id>', DownloadView.as_view(), name='download'),
]