# from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    path('users/', views.user_list, name='user_list'),
    path('users/follow/', views.user_follow, name='user_follow'),
    path('users/<int:user_id>/followers/', views.user_followers_list, name='user_followers_list'),  # Новый маршрут для получения списка подписчиков
    path('users/<username>/', views.user_detail, name='user_detail'),
    path('users/<str:username>/movies/', views.user_movie_list, name='user_movie_list'),
    path('ranking/', views.user_ranking, name='user_ranking'),  # Новый маршрут для рейтинга пользователей
]