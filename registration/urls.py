from django.urls import path
from . import views

app_name = 'registration'
urlpatterns = [
    path('', views.ScrapeTargetListView.as_view(), name='targets'),
    #path('targets/', views.ScrapeTargetListView.as_view(), name='targets'),
    path('create/', views.ScrapeTargetCreateView.as_view(), name='create'),
    path('update/<int:pk>', views.ScrapeTargetUpdateView.as_view(), name='update'),
    path('results/<int:target_id>/', views.ScrapeResultListView.as_view(), name='results'),
    path('results/delete/<int:pk>/', views.ScrapeResultDeleteView.as_view(), name='del_results'),
]