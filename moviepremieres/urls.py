from django.urls import path
from . import views

app_name = 'moviepremieres'

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('<slug:slug>/', views.movie_detail, name='movie_detail'),
]