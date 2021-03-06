from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

app_name = 'accounts'
urlpatterns = [
    path('', views.LoginView.as_view(), name='top'),
    # path('login/', views.LoginView.as_view(), name='login'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('create/', views.CreateAccountView.as_view(), name='create'),
]