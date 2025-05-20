from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Movie

def movie_list(request):
    movies = Movie.objects.all()  # Получаем все фильмы
    return render(request, 'moviepremieres/movie_list.html', {'section': 'moviepremieres', 'movies': movies})

def movie_detail(request, slug):
    movie = get_object_or_404(Movie, slug=slug)
    return render(request, 'moviepremieres/movie_detail.html', {'movie': movie})