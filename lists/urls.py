# movie_lists/urls.py
from django.urls import path
from . import views

app_name = 'lists'

urlpatterns = [
    path('create/', views.create_movie_list, name='create_movie_list'),
    path('<int:list_id>/', views.movie_list_detail, name='movie_list_detail'),
    path('<int:list_id>/like/', views.like_movie_list, name='like_movie_list'),
    path('add/<int:list_id>/', views.add_movies_to_list, name='add_movies_to_list'),
    path('view/<int:list_id>/', views.view_movie_list, name='view_movie_list'),
    path('users_lists/', views.users_movie_lists, name='users_movie_lists'),
]