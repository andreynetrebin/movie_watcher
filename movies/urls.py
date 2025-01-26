from django.urls import path
from . import views
app_name = 'movies'
urlpatterns = [
    path('create/', views.movie_create, name='create'),
    path('detail/<slug:slug>/', views.movie_detail, name='detail'),
    # path('like/', views.movie_like, name='like'),
    path('mark_like/', views.mark_like, name='mark_like'),
    path('mark_dislike/', views.mark_dislike, name='mark_dislike'),
    path('mark_watched/', views.mark_watched, name='mark_watched'),
    path('mark_recently_watched/', views.mark_recently_watched, name='mark_recently_watched'),
    # path('toggle_wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.add_to_wishlist, name='wishlist'),
    path('', views.movie_list, name='list'),

    path('create_list/', views.create_movie_list, name='create_movie_list'),
    path('list/<int:list_id>/', views.movie_list_detail, name='movie_list_detail'),
    path('list/<int:list_id>/like/', views.like_movie_list, name='like_movie_list'),
    path('list/<int:list_id>/add/<int:movie_id>/', views.add_movie_to_list, name='add_movie_to_list'),
    path('all-movie-lists/', views.all_movie_lists, name='all_movie_lists'),
    path('movie-actions/', views.movie_actions, name='movie_actions'),
    path('directors/', views.director_list, name='director_list'),
    path('writers/', views.writer_list, name='writer_list'),
    path('directors/<int:pk>/', views.director_detail, name='director_detail'),
    path('writers/<int:pk>/', views.writer_detail, name='writer_detail'),
]



