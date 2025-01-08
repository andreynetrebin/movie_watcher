from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from .forms import MovieCreateForm
from .models import Movie, Genre, Country, Director, Writer
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, \
PageNotAnInteger
from actions.utils import create_action


@login_required
@require_POST
def movie_like(request):
    movie_id = request.POST.get('id')
    action = request.POST.get('action')
    if movie_id and action:
        try:
            movie = Movie.objects.get(id=movie_id)
            if action == 'like':
                if movie.users_like.filter(id=request.user.id).exists():
                    return JsonResponse({'status': 'exists'})
                if movie.users_dislike.filter(id=request.user.id).exists():
                    movie.users_dislike.remove(request.user)  # Удаляем dislike, если он есть

                movie.users_like.add(request.user)  # Добавляем like
                create_action(request.user, 'likes', movie)

            if action == 'dislike':
                if movie.users_dislike.filter(id=request.user.id).exists():
                    return JsonResponse({'status': 'exists'})
                if movie.users_like.filter(id=request.user.id).exists():
                    movie.users_like.remove(request.user)  #  Удаляем like, если он есть
                movie.users_dislike.add(request.user)  # Добавляем dislike
                create_action(request.user, 'dislikes', movie)
            return JsonResponse({'status': 'ok'})
        except Movie.DoesNotExist:
            pass
    return JsonResponse({'status': 'error'})


# @login_required
# def toggle_watchlist(request, movie_id):
#     movie = get_object_or_404(Movie, id=movie_id)
#     watchlist_item, created = Watchlist.objects.get_or_create(user=request.user, movie=movie)
#
#     if not created:
#         watchlist_item.delete()  # Удаляем из watchlist, если он уже был
#     return redirect('movie_list')

@login_required
def movie_create(request):
    # print(request)
    if request.method == 'POST':
    # form is sent
        form = MovieCreateForm(data=request.POST)
        if form.is_valid():
    # form data is valid
            print("view")
            cd = form.cleaned_data
            # genres = []
            for genre in cd["genres"]:
                if not Genre.objects.filter(name=genre).exists():
                    genre_row = Genre.objects.create(name=genre)
                    genre_row.save()
            for country in cd["countries"]:
                if not Country.objects.filter(name=country).exists():
                    country_row = Country.objects.create(name=country)
                    country_row.save()


            for director in cd["directors"]:
                if not Director.objects.filter(staff_id=director["staff_id"]).exists():
                    director_row = Director.objects.create(name=director["name"], staff_id=director["staff_id"])
                    director_row.save()
            for writer in cd["writers"]:
                if not Writer.objects.filter(staff_id=writer["staff_id"]).exists():
                    writer_row = Writer.objects.create(name=writer["name"], staff_id=writer["staff_id"])
                    writer_row.save()

            # print(genres)

            new_movie = form.save(commit=False)
    # # assign current user to the item
            new_movie.user = request.user
            new_movie.title = cd["title"]
            new_movie.title_original = cd["title_original"]
            new_movie.year = cd["year"]
            new_movie.duration = cd["duration"]
            # new_movie.director = cd["director"]
            new_movie.kinopoisk_id = cd["kinopoisk_id"]
            new_movie.kinopoisk_url = cd["kinopoisk_url"]
            new_movie.url = cd["url"]
            new_movie.description = cd["description"]
            new_movie.movie_json = cd["movie_data"]
            new_movie.movie_staff_json = cd["movie_staff_data"]

            new_movie.save()
            create_action(request.user, 'added movie', new_movie)
            for genre in cd["genres"]:
                genre_row = Genre.objects.get(name=genre)
                new_movie.genres.add(genre_row)
            for country in cd["countries"]:
                country_row = Country.objects.get(name=country)
                new_movie.countries.add(country_row)

            for director in cd["directors"]:
                director_row = Director.objects.get(staff_id=director["staff_id"])
                new_movie.directors.add(director_row)
            for writer in cd["writers"]:
                writer_row = Writer.objects.get(staff_id=writer["staff_id"])
                new_movie.writers.add(writer_row)

        messages.success(request, 'Movie added successfully')
    # redirect to new created item detail view
        return redirect(new_movie.get_absolute_url())
    else:
    # build form with data provided by the bookmarklet via GET
        form = MovieCreateForm(data=request.GET)
    return render(
          request,
            'movies/movie/create.html',
            {'section': 'movies', 'form': form}
    )


def movie_detail(request, slug):
    movie = get_object_or_404(Movie, slug=slug)
    return render(request,
                  'movies/movie/detail.html',
                  {'section': 'movies',
                   'movie': movie})

@login_required
def movie_list(request):
    movies = Movie.objects.all()
    paginator = Paginator(movies, 8)
    page = request.GET.get('page')
    movies_only = request.GET.get('movies_only')
    try:
        movies = paginator.page(page)
    except PageNotAnInteger:
    # Если страница не является целым числом,
    # то доставить первую страницу
        movies = paginator.page(1)
    except EmptyPage:
        if movies_only:
        # Если AJAX-запрос и страница вне диапазона,
        # то вернуть пустую страницу
            return HttpResponse('')
    # Если страница вне диапазона,
    # то вернуть последнюю страницу результатов
        movies = paginator.page(paginator.num_pages)
    if movies_only:
        return render(request,
    'movies/movie/list_movies.html',
    {'section': 'movies',
    'movies': movies})

    return render(request,
    'movies/movie/list.html',
    {'section': 'movies',
    'movies': movies})