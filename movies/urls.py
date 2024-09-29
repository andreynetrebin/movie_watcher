from django.urls import path
from . import views
app_name = 'movies'
urlpatterns = [
    path('create/', views.movie_create, name='create'),
    path('detail/<slug:slug>/', views.movie_detail, name='detail'),
    path('like/', views.movie_like, name='like'),
]