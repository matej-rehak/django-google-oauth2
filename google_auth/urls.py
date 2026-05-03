from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('auth/login/', views.login_view, name='google_login'),
    path('auth/callback/', views.callback_view, name='google_callback'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('auth/logout/', views.logout_view, name='logout'),
]
