from django.urls import path

from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/login/', views.login_redirect, name='login'),
    path('auth/callback/', views.auth_callback, name='auth_callback'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),
    path('book-first-available/', views.book_first_available_view, name='book_first_available'),
]
