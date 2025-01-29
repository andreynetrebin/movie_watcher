from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from .forms import MovieCreateForm, CommentForm, MovieBulkCreateForm
from django.db.models import Count
from .models import Movie, Genre, Country, Director, Writer, Watched, WishList, MovieList
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, \
PageNotAnInteger
from actions.utils import create_action
from actions.models import Action
from django.views.generic import ListView, DetailView

def director_list(request):
    # Получаем всех режиссеров с количеством фильмов, исключая тех, у кого 0 фильмов
    directors = Director.objects.annotate(num_movies=Count('movies_director')).filter(num_movies__gt=0).order_by('-num_movies')

    # Пагинация
    paginator = Paginator(directors, 20)  # 20 режиссеров на странице
    page_number = request.GET.get('page')
    directors_page = paginator.get_page(page_number)

    return render(request, 'movies/directors/director_list.html', {'directors': directors_page})

def writer_list(request):
    # Получаем всех сценаристов с количеством фильмов, исключая тех, у кого 0 фильмов
    writers = Writer.objects.annotate(num_movies=Count('movies_writer')).filter(num_movies__gt=0).order_by('-num_movies')

    # Пагинация
    paginator = Paginator(writers, 20)  # 20 сценаристов на странице
    page_number = request.GET.get('page')
    writers_page = paginator.get_page(page_number)

    return render(request, 'movies/writers/writer_list.html', {'writers': writers_page})

@login_required
def movie_bulk_create(request):
    if request.method == 'POST':
        form = MovieBulkCreateForm(data=request.POST)
        if form.is_valid():
            urls = form.cleaned_data['urls'].strip().splitlines()
            print(urls)
            for url in urls:
                url = url.strip()
                if url:  # Проверяем, что строка не пустая
                    print(url)
                    try:
                        # Здесь вы можете использовать вашу существующую логику для обработки одного URL
                        # Например, вы можете создать временный объект формы для обработки URL
                        movie_form = MovieCreateForm(data={'url': url})
                        if movie_form.is_valid():
                            cd = movie_form.cleaned_data
                            print(cd)
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
                            new_movie = movie_form.save(commit=False)

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
                            print("before message success")
#                            messages.success(request, f'Фильм из {url} добавлен успешно.')

                        else:
                            print("error")

#                            messages.error(request, f'Ошибка при добавлении фильма из {url}: {movie_form.errors}')
                    except Exception as e:
                        print(f'Ошибка при добавлении фильма из {url}: {str(e)}')
                        messages.error(request, f'Ошибка при добавлении фильма из {url}: {str(e)}')
            return redirect('movies:list')  # Перенаправление на список фильмов или другую страницу
    else:
        form = MovieBulkCreateForm()

    return render(request, 'movies/movie/bulk_create.html', {'form': form})


def director_detail(request, pk):
    director = get_object_or_404(Director, pk=pk)
    # Получаем все фильмы, связанные с этим режиссером, отсортированные по году в порядке убывания
    movies = director.movies_director.all().order_by('-year')

    return render(request, 'movies/directors/director_detail.html', {
        'director': director,
        'movies': movies,
    })

def writer_detail(request, pk):
    writer = get_object_or_404(Writer, pk=pk)
    # Получаем все фильмы, связанные с этим сценаристом, отсортированные по году в порядке убывания
    movies = writer.movies_writer.all().order_by('-year')

    return render(request, 'movies/writers/writer_detail.html', {
        'writer': writer,
        'movies': movies,
    })

def movie_actions(request):
    # Извлекаем все действия
    actions = Action.objects.filter(target_ct__model='movie').select_related('user').all()
    # Пагинация
    paginator = Paginator(actions, 10)  # 10 действий на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Топ-10 фильмов по количеству просмотренных
    top_movies = Movie.objects.annotate(num_watched=Count('watched')).order_by('-num_watched')[:10]
    # Топ-10 пользователей по количеству просмотренных фильмов
    top_users = User.objects.annotate(num_watched=Count('watched')).order_by('-num_watched')[:10]

    return render(
        request,
        'movies/movie/movie_actions.html',
        {
            'section': 'movie_actions',
             'actions': page_obj,
            'top_movies': top_movies,
            'top_users': top_users,
}
    )

@login_required
def all_movie_lists(request):
    # Получаем все списки фильмов, созданные всеми пользователями
    movie_lists = MovieList.objects.prefetch_related('movies')
    return render(request, 'movies/user_movies_lists/all_movie_lists.html', {
        'movie_lists': movie_lists,
    })

@login_required
def add_movie_to_list(request, list_id, movie_id):
    movie_list = get_object_or_404(MovieList, id=list_id, user=request.user)
    movie = get_object_or_404(Movie, id=movie_id)

    if movie not in movie_list.movies.all():
        movie_list.movies.add(movie)
        movie_list.add_points(1)  # Награда за добавление фильма
    return redirect('movies:movie_list_detail', list_id)

@login_required
def create_movie_list(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        movie_list = MovieList.objects.create(user=request.user, title=title)
        movie_list.add_points(10)  # Награда за создание списка
        return redirect('movies:movie_list_detail', movie_list.id)
    return render(request, 'movies/user_movies_lists/create_movie_list.html')

@login_required
def movie_list_detail(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id)
    all_movies = Movie.objects.all()  # Получаем все фильмы
    return render(request, 'movies/user_movies_lists/movie_list_detail.html', {'movie_list': movie_list, 'all_movies': all_movies})
@login_required
def like_movie_list(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id)
    if request.user in movie_list.users_like.all():
        movie_list.users_like.remove(request.user)
        movie_list.add_points(-5)  # Уменьшение баллов за удаление лайка
    else:
        movie_list.users_like.add(request.user)
        movie_list.add_points(5)  # Награда за лайк
    return redirect('movies/movie/movie_list_detail.html', list_id)

@login_required
@require_POST
def mark_watched(request):
    if request.method == 'POST':
        movie_id = request.POST.get('id')
        movie = get_object_or_404(Movie, id=movie_id)
        # Проверяем, был ли фильм уже просмотрен
        watched, created = Watched.objects.get_or_create(user=request.user, movie=movie)
        if not created:
            watched.delete()  # Удаляем из просмотренных, если он уже был
            return JsonResponse({'status': 'removed'})
        return JsonResponse({'status': 'added'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
@require_POST
def mark_recently_watched(request):
    if request.method == 'POST':
        movie_id = request.POST.get('id')
        movie = get_object_or_404(Movie, id=movie_id)
        # Проверяем, был ли фильм уже просмотрен
        watched, created = Watched.objects.get_or_create(user=request.user, movie=movie)
        if not created:
            watched.delete()  # Удаляем из просмотренных, если он уже был
            return JsonResponse({'status': 'removed'})
        create_action(request.user, 'отметил как недавно просмотренный', movie)  # Вызываем сигнал для "просмотрен недавно"
        return JsonResponse({'status': 'added'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# views.py
@login_required
@require_POST
def add_to_wishlist(request):
    if request.method == 'POST':
        movie_id = request.POST.get('id')
        movie = get_object_or_404(Movie, id=movie_id)

        # Проверяем, добавлен ли фильм в вишлист
        wishlist_item, created = WishList.objects.get_or_create(user=request.user, movie=movie)

        if created:
            create_action(request.user, 'добавил в вотчлист',
                          movie)  # Вызываем сигнал для "просмотрен недавно"
            return JsonResponse({'status': 'added'})
        else:
            wishlist_item.delete()
            return JsonResponse({'status': 'removed'})

    return JsonResponse({'status': 'error'}, status=400)


@login_required
@require_POST
def mark_like(request):
    if request.method == 'POST':
        movie_id = request.POST.get('id')
        movie = get_object_or_404(Movie, id=movie_id)
        movie.add_like(request.user)
        create_action(request.user, 'понравился', movie)
        return JsonResponse({'status': 'liked', 'total_likes': movie.total_likes})
@login_required
@require_POST
def mark_dislike(request):
    if request.method == 'POST':
        movie_id = request.POST.get('id')
        movie = get_object_or_404(Movie, id=movie_id)
        movie.add_dislike(request.user)
        create_action(request.user, 'не понравился', movie)
        return JsonResponse({'status': 'disliked', 'total_dislikes': movie.total_dislikes})


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
            create_action(request.user, 'добавил', new_movie)
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
    comments = movie.comments.filter(active=True)
    # Получаем количество пользователей, пометивших фильм как просмотренный
    watched_count = Watched.objects.filter(movie=movie).count()
    # Вычисляем соотношения
    like_ratio = movie.total_likes / watched_count if watched_count > 0 else 0
    dislike_ratio = movie.users_dislike.count() / movie.users_like.count() if movie.users_like.count() > 0 else 0
    if request.method == 'POST':
        form = CommentForm(data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.movie = movie
            comment.author = request.user
            comment.save()
            create_action(request.user, 'оставил комментарий', movie)
            return redirect(movie.get_absolute_url())  # Перенаправление на страницу фильма
    else:
        form = CommentForm()

    return render(request,
                  'movies/movie/detail.html',
                  {'section': 'movies',
                   'movie': movie,
                   'watched_count': watched_count,
                   'like_ratio': like_ratio,
                   'dislike_ratio': dislike_ratio,
                   'comments': comments,
                   'form': form})

    # return render(request, 'movies/movie_detail.html', {
    #     'movie': movie,
    #     'comments': comments,
    #     'form': form,
    #
    # })

@login_required
def movie_list(request):
    user = request.user
    movies = Movie.objects.all()  # Получаем все фильмы по умолчанию
    wishlist_movies = WishList.objects.filter(user=request.user).values_list('movie_id',
                                                                             flat=True)
    # Фильтрация по вкладкам
    filter_type = request.GET.get('filter', 'all')  # Получаем тип фильтра из параметров запроса

    if filter_type == 'watched':
        movies = movies.filter(watched__user=user)  # Предполагается, что у вас есть модель Watched
    elif filter_type == 'unwatched':
        movies = movies.exclude(watched__user=user)
    elif filter_type == 'liked':
        movies = movies.filter(users_like=user)
    elif filter_type == 'disliked':
        movies = movies.filter(users_dislike=user)
    elif filter_type == 'watchlist':
        movies = movies.filter(wishlist__user=user)  # Предполагается, что у вас есть модель WishList
    elif filter_type == 'added':
        movies = movies.filter(user=user)

    # Получаем список просмотренных фильмов для текущего пользователя

    watched_movies = Watched.objects.filter(user=user).values_list('movie_id', flat=True)

    # Пагинация
    paginator = Paginator(movies, 10)  # Показывать 10 фильмов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Получаем топ-10 режиссеров и сценаристов
    top_directors = Director.objects.annotate(num_movies=Count('movies_director')).order_by('-num_movies')[:10]
    top_writers = Writer.objects.annotate(num_movies=Count('movies_writer')).order_by('-num_movies')[:10]

    return render(request, 'movies/movie/list.html', {
        'page_obj': page_obj,
        'top_directors': top_directors,
        'top_writers': top_writers,
        'filter_type': filter_type,
        'watched_movies': watched_movies,  # Передаем список просмотренных фильмов
        'wishlist_movies': wishlist_movies,
    })


