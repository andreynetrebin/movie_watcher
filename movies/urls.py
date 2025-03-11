from django.urls import path
from . import views
app_name = 'movies'
urlpatterns = [
    path('create/', views.movie_create, name='create'),
    path('detail/<slug:slug>/', views.movie_detail, name='detail'),
    path('bulk_create/', views.movie_bulk_create, name='movie_bulk_create'),
    path('mark_like/', views.mark_like, name='mark_like'),
    path('mark_dislike/', views.mark_dislike, name='mark_dislike'),
    path('mark_watched/', views.mark_watched, name='mark_watched'),
    path('mark_recently_watched/', views.mark_recently_watched, name='mark_recently_watched'),
    path('wishlist/', views.add_to_wishlist, name='wishlist'),
    path('', views.movie_list, name='list'),
    path('directors/', views.director_list, name='director_list'),
    path('writers/', views.writer_list, name='writer_list'),
    path('directors/<int:pk>/', views.director_detail, name='director_detail'),
    path('writers/<int:pk>/', views.writer_detail, name='writer_detail'),
    path('search/', views.search_movies, name='search_movies'),
]



