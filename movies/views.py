from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from .forms import MovieCreateForm
from .models import Movie, Genre, Country, Director, Writer
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
@require_POST
def movie_like(request):
    movie_id = request.POST.get('id')
    action = request.POST.get('action')
    if movie_id and action:
        try:
            movie = Movie.objects.get(id=movie_id)
            if action == 'like':
                movie.users_like.add(request.user)
            else:
                movie.users_like.remove(request.user)
            return JsonResponse({'status': 'ok'})
        except Movie.DoesNotExist:
            pass
        return JsonResponse({'status': 'error'})



# Create your views here.

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