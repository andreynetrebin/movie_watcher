from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
import logging
from django.shortcuts import get_object_or_404
from .forms import MovieCreateForm, CommentForm, MovieBulkCreateForm
from django.db.models import Count, Q, FloatField, ExpressionWrapper
from .models import Movie, Genre, Country, Director, Writer, Watched, WishList, MovieList
from versioning.models import Version
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, \
PageNotAnInteger
from actions.utils import create_action
from actions.models import Action

logger = logging.getLogger(__name__)

def search_movies(request):
    if 'query' in request.GET:
        query = request.GET['query']
        movies = Movie.objects.filter(title__icontains=query)[:10]  # Ограничиваем до 10 результатов
        results = [{'id': movie.id, 'title': movie.title, 'slug': movie.slug, 'year': movie.year} for movie in movies]
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)
@login_required
def director_list(request):
    user = request.user

    # Получаем всех режиссеров с количеством фильмов, исключая тех, у кого 0 фильмов
    directors = Director.objects.annotate(
        num_movies=Count('movies_director', distinct=True),  # Количество уникальных фильмов у каждого режиссера
        num_watched=Count('movies_director__watched', filter=Q(movies_director__watched__user=user)),  # Количество просмотренных фильмов
        watched_percentage=ExpressionWrapper(
            Count('movies_director__watched', filter=Q(movies_director__watched__user=user)) * 100.0 / Count('movies_director', distinct=True),
            output_field=FloatField()
        )
    ).filter(num_movies__gt=0).order_by('-num_movies')

    # Пагинация
    paginator = Paginator(directors, 20)  # 20 режиссеров на странице
    page_number = request.GET.get('page')
    directors_page = paginator.get_page(page_number)

    return render(request, 'movies/directors/director_list.html', {'directors': directors_page})

@login_required
def writer_list(request):
    user = request.user

    # Получаем всех сценаристов с количеством фильмов, исключая тех, у кого 0 фильмов
    writers = Writer.objects.annotate(
        num_movies=Count('movies_writer', distinct=True),  # Количество уникальных фильмов у каждого сценариста
        num_watched=Count('movies_writer__watched', filter=Q(movies_writer__watched__user=user)),  # Количество просмотренных фильмов
        watched_percentage=ExpressionWrapper(
            Count('movies_writer__watched', filter=Q(movies_writer__watched__user=user)) * 100.0 / Count('movies_writer', distinct=True),
            output_field=FloatField()
        )
    ).filter(num_movies__gt=0).order_by('-num_movies')

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


@login_required
def director_detail(request, pk):
    director = get_object_or_404(Director, pk=pk)
    # Получаем все фильмы, связанные с этим режиссером, отсортированные по году в порядке убывания
    movies = director.movies_director.all().order_by('-year')
    wishlist_movies = WishList.objects.filter(user=request.user).values_list('movie_id', flat=True)
    watched_movies = Watched.objects.filter(user=request.user).values_list('movie_id', flat=True)

    return render(request, 'movies/directors/director_detail.html', {
        'director': director,
        'movies': movies,
        'watched_movies': watched_movies,
        'wishlist_movies': wishlist_movies,
    })

@login_required
def writer_detail(request, pk):
    writer = get_object_or_404(Writer, pk=pk)
    # Получаем все фильмы, связанные с этим сценаристом, отсортированные по году в порядке убывания
    movies = writer.movies_writer.all().order_by('-year')
    wishlist_movies = WishList.objects.filter(user=request.user).values_list('movie_id', flat=True)
    watched_movies = Watched.objects.filter(user=request.user).values_list('movie_id', flat=True)

    return render(request, 'movies/writers/writer_detail.html', {
        'writer': writer,
        'movies': movies,
        'watched_movies': watched_movies,
        'wishlist_movies': wishlist_movies,
    })


def movie_actions(request):
    # Извлекаем все действия, включая подписки
    actions = Action.objects.filter(
        Q(target_ct__model='movie') | Q(verb__in=['подписался', 'отписался'])
    ).select_related('user').all()

    # Пагинация
    paginator = Paginator(actions, 10)  # 10 действий на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Топ 5 фильмов по количеству лайков
    top_movies = Movie.objects.annotate(likes_count=Count('users_like')).order_by('-likes_count')[:5]

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
    movie_lists = MovieList.objects.prefetch_related('movies', 'user')

    # Получаем список ID фильмов, просмотренных текущим пользователем
    watched_movies = Watched.objects.filter(user=request.user).values_list('movie_id', flat=True)

    # Подсчитываем количество просмотренных фильмов для каждого списка
    for movie_list in movie_lists:
        movie_list.watched_count = sum(1 for movie in movie_list.movies.all() if movie.id in watched_movies)
        movie_list.total_count = movie_list.movies.count()
        movie_list.watched_percentage = (movie_list.watched_count / movie_list.total_count * 100) if movie_list.total_count > 0 else 0

    return render(request, 'movies/user_movies_lists/all_movie_lists.html', {
        'movie_lists': movie_lists,
    })




def add_movies_to_list(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id)
    movies = Movie.objects.all()

    # Фильтрация по названию
    search_query = request.GET.get('search', '')
    if search_query:
        movies = movies.filter(title__icontains=search_query)

    # Сортировка
    sort_by = request.GET.get('sort', 'created')
    order = request.GET.get('order', 'asc')

    if sort_by == 'title':
        movies = movies.order_by('title' if order == 'asc' else '-title')
    elif sort_by == 'year':
        movies = movies.order_by('year' if order == 'asc' else '-year')
    elif sort_by == 'created':
        movies = movies.order_by('created' if order == 'asc' else '-created')

    # Пагинация
    paginator = Paginator(movies, 10)  # 10 фильмов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        selected_movies = request.POST.getlist('movies')
        for movie_id in selected_movies:
            movie_list.movies.add(Movie.objects.get(id=movie_id))
        # Остаемся на той же странице после добавления
        return render(request, 'movies/user_movies_lists/add_movies_to_list.html', {
            'movie_list': movie_list,
            'page_obj': page_obj,
            'search_query': search_query,
        })

    return render(request, 'movies/user_movies_lists/add_movies_to_list.html', {
        'movie_list': movie_list,
        'page_obj': page_obj,
        'search_query': search_query,
    })
@login_required  # Убедитесь, что пользователь аутентифицирован
def create_movie_list(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        movie_list = MovieList.objects.create(title=title, user=request.user)
        return redirect('movies:add_movies_to_list', list_id=movie_list.id)
    return render(request, 'movies/user_movies_lists/create_movie_list.html')



def view_movie_list(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id)

    if request.method == 'POST':
        if 'save_list' in request.POST:
            # Логика для сохранения списка (если это необходимо)
            return redirect('movies:movie_list_detail', list_id=list_id)  # Перенаправляем на страницу созданного списка
        elif 'clear_list' in request.POST:
            # Очистка списка
            movie_list.movies.clear()  # Удаляем все фильмы из списка
            return redirect('movies:add_movies_to_list', list_id=movie_list.id)  # Перенаправляем на страницу добавления фильмов

    return render(request, 'movies/user_movies_lists/view_movie_list.html', {'movie_list': movie_list})

@login_required
def movie_list_detail(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id)

    # Получаем все фильмы в списке
    movies = movie_list.movies.all().order_by('-year')
    wishlist_movies = WishList.objects.filter(user=request.user).values_list('movie_id', flat=True)
    watched_movies = Watched.objects.filter(user=request.user).values_list('movie_id', flat=True)

    # Получаем список ID просмотренных фильмов текущим пользователем


    return render(request, 'movies/user_movies_lists/movie_list_detail.html', {
        'movie_list': movie_list,
        'movies': movies,
        'watched_movies': watched_movies,
        'wishlist_movies': wishlist_movies,
        'can_edit': request.user == movie_list.user,  # Проверяем, может ли текущий пользователь редактировать список
    })

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
        movie_url = request.build_absolute_uri(movie.get_absolute_url())
        create_action(request.user, 'недавно посмотрел', target=movie, movie_url=movie_url)  # Вызываем сигнал для "просмотрен нед>
        return JsonResponse({'status': 'added'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
@require_POST
def add_to_wishlist(request):
    if request.method == 'POST':
        movie_id = request.POST.get('id')
        movie = get_object_or_404(Movie, id=movie_id)
        # Проверяем, добавлен ли фильм в вишлист
        wishlist_item, created = WishList.objects.get_or_create(user=request.user, movie=movie)
        if created:
            movie_url = request.build_absolute_uri(movie.get_absolute_url())
            create_action(request.user, 'добавил в "Буду смотреть"', target=movie, movie_url=movie_url)
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
        movie_url = request.build_absolute_uri(movie.get_absolute_url())
        create_action(request.user, 'понравился', target=movie, movie_url=movie_url)

        return JsonResponse({'status': 'liked', 'total_likes': movie.total_likes})

@login_required
@require_POST
def mark_dislike(request):
    if request.method == 'POST':
        movie_id = request.POST.get('id')
        movie = get_object_or_404(Movie, id=movie_id)
        movie.add_dislike(request.user)
        movie_url = request.build_absolute_uri(movie.get_absolute_url())
        create_action(request.user, 'не понравился', target=movie, movie_url=movie_url)

        return JsonResponse({'status': 'disliked', 'total_dislikes': movie.total_dislikes})


@login_required
def movie_create(request):
    if request.method == 'POST':
        form = MovieCreateForm(data=request.POST, source='website')
        if form.is_valid():
            cd = form.cleaned_data

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
            new_movie = form.save(commit=False)
            new_movie.user = request.user
            new_movie.title = cd["title"]
            new_movie.title_original = cd["title_original"]
            new_movie.year = cd["year"]
            new_movie.duration = cd["duration"]
            new_movie.kinopoisk_id = cd["kinopoisk_id"]
            new_movie.kinopoisk_url = cd["kinopoisk_url"]
            new_movie.url = cd["url"]
            new_movie.description = cd["description"]
            new_movie.movie_json = cd["movie_data"]
            new_movie.movie_staff_json = cd["movie_staff_data"]
            new_movie.movie_data = cd["movie_data"]
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
            movie_url = request.build_absolute_uri(new_movie.get_absolute_url())
            create_action(request.user, 'добавил', target=new_movie, movie_url=movie_url)
            return redirect(new_movie.get_absolute_url())
    else:
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
            movie_url = request.build_absolute_uri(movie.get_absolute_url())
            create_action(request.user, 'прокомментировал', movie)

            return redirect(movie.get_absolute_url())  # Перенаправление на страницу фильма
    else:
        form = CommentForm()  # Инициализация формы, если это не POST-запрос

    return render(request, 'movies/movie/detail.html', {
        'section': 'movies',
        'movie': movie,
        'watched_count': watched_count,
        'like_ratio': like_ratio,
        'dislike_ratio': dislike_ratio,
        'comments': comments,
        'form': form
    })


@login_required
def movie_list(request):
    user = request.user
    movies = Movie.objects.all()  # Получаем все фильмы по умолчанию
    wishlist_movies = WishList.objects.filter(user=request.user).values_list('movie_id', flat=True)

    # Фильтрация по вкладкам
    filter_type = request.GET.get('filter', 'all')  # Получаем тип фильтра из параметров запроса

    # Фильтрация по статусу
    if filter_type == 'watched':
        movies = movies.filter(watched__user=user)
    elif filter_type == 'unwatched':
        movies = movies.exclude(watched__user=user)
    elif filter_type == 'liked':
        movies = movies.filter(users_like=user)
    elif filter_type == 'disliked':
        movies = movies.filter(users_dislike=user)
    elif filter_type == 'watchlist':
        movies = movies.filter(wishlist__user=user)
    elif filter_type == 'added':
        movies = movies.filter(user=user)

    # Фильтрация по названию и оригинальному названию
    title_filter = request.GET.get('title', '')
    if title_filter:
        movies = movies.filter(title__icontains=title_filter) | movies.filter(title_original__icontains=title_filter)

    # Фильтрация по Кинопоиск ID
    kinopoisk_id_filter = request.GET.get('kinopoisk_id', '')
    if kinopoisk_id_filter:
        movies = movies.filter(kinopoisk_id=kinopoisk_id_filter)

    # Фильтрация по жанрам
    genre_filter = request.GET.getlist('genres')  # Получаем список выбранных жанров
    genre_filter = [genre for genre in genre_filter if genre]  # Удаляем пустые значения
    if genre_filter:
        movies = movies.filter(genres__id__in=genre_filter).annotate(num_genres=Count('genres')).filter(
            num_genres=len(genre_filter)).distinct()

    # Сортировка
    sort_by = request.GET.get('sort', 'created')  # По умолчанию сортируем по дате создания
    if sort_by == 'year':
        movies = movies.order_by('year')
    elif sort_by == 'created':
        movies = movies.order_by('-created')
    elif sort_by == 'title':
        movies = movies.order_by('title')  # Сортировка по названию

    # Получаем список просмотренных фильмов для текущего пользователя
    watched_movies = Watched.objects.filter(user=user).values_list('movie_id', flat=True)

    # Пагинация
    paginator = Paginator(movies, 10)  # Показывать 10 фильмов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Логирование для диагностики
    logger.info(f"Page number: {page_number}, Movies on this page: {page_obj.object_list}")

    # Получаем топ-10 режиссеров и сценаристов
    top_directors = Director.objects.annotate(num_movies=Count('movies_director')).order_by('-num_movies')[:10]
    top_writers = Writer.objects.annotate(num_movies=Count('movies_writer')).order_by('-num_movies')[:10]

    # Получаем все жанры для отображения в фильтре
    all_genres = Genre.objects.all()

    return render(request, 'movies/movie/list.html', {
        'page_obj': page_obj,
        'top_directors': top_directors,
        'top_writers': top_writers,
        'filter_type': filter_type,
        'watched_movies': watched_movies,
        'wishlist_movies': wishlist_movies,
        'title_filter': title_filter,  # Передаем фильтр названия в шаблон
        'kinopoisk_id_filter': kinopoisk_id_filter,  # Передаем фильтр по Кинопоиск ID в шаблон
        'all_genres': all_genres,  # Передаем все жанры в шаблон
        'selected_genres': genre_filter,  # Передаем выбранные жан ры в шаблон
        'sort_by': sort_by,  # Передаем выбранный параметр сортировки в шаблон
    })