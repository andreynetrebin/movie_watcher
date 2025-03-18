from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Count, Q, FloatField, ExpressionWrapper
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import logging
from .forms import MovieCreateForm, CommentForm, MovieBulkCreateForm
from .models import Movie, Genre, Country, Director, Writer, Watched, WishList
from lists.models import MovieList
from actions.utils import create_action
from actions.models import Action
from account.models import Profile
from account.points_manager import PointsManager

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
            success_count = 0  # Счетчик успешно добавленных фильмов
            for url in urls:
                url = url.strip()
                if url:  # Проверяем, что строка не пустая
                    try:
                        # Создаем временный объект формы для обработки URL
                        movie_form = MovieCreateForm(data={'url': url}, source='website')
                        if movie_form.is_valid():
                            cd = movie_form.cleaned_data

                            # Проверяем, существует ли фильм
                            if isinstance(cd['url'], dict) and 'exists' in cd['url']:
                                existing_movie = cd['url']['movie']
                                messages.info(request, f'Фильм {existing_movie.title} уже есть в базе данных.')
                                continue  # Переходим к следующему URL

                            # Обработка жанров
                            for genre in cd["genres"]:
                                if not Genre.objects.filter(name=genre).exists():
                                    Genre.objects.create(name=genre)

                            # Обработка стран
                            for country in cd["countries"]:
                                if not Country.objects.filter(name=country).exists():
                                    Country.objects.create(name=country)

                            # Обработка режиссеров
                            for director in cd["directors"]:
                                if not Director.objects.filter(staff_id=director["staff_id"]).exists():
                                    Director.objects.create(name=director["name"], staff_id=director["staff_id"])

                            # Обработка сценаристов
                            for writer in cd["writers"]:
                                if not Writer.objects.filter(staff_id=writer["staff_id"]).exists():
                                    Writer.objects.create(name=writer["name"], staff_id=writer["staff_id"])

                            # Сохранение фильма
                            new_movie = movie_form.save(commit=False)  # Сохраняем объект, но не в БД
                            new_movie.user = request.user  # Устанавливаем пользователя
                            new_movie.save()  # Сохраняем изменения

                            # Добавление связей
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

                            success_count += 1  # Увеличиваем счетчик успешных добавлений
                        else:
                            messages.error(request, f'Ошибка при добавлении фильма из {url}: {movie_form.errors}')
                    except Exception as e:
                        print(f'Ошибка при добавлении фильма из {url}: {str(e)}')
                        messages.error(request, f'Ошибка при добавлении фильма из {url}: {str(e)}')

            # Сообщение об успешном добавлении
            messages.success(request, f'Успешно добавлено {success_count} фильмов.')
            return redirect('movies:list')  # Перенаправление на список фильмов

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

    # Топ 3 пользователей по баллам
    top_users = Profile.objects.select_related('user').order_by('-points')[:3]

    # Топ 3 списков фильмов по количеству лайков
    top_lists = MovieList.objects.annotate(likes_count=Count('users_like')).order_by('-likes_count')[:3]

    return render(
        request,
        'movies/movie/movie_actions.html',
        {
            'section': 'movie_actions',
            'actions': page_obj,
            'top_movies': top_movies,
            'top_users': top_users,  # Передаем топ-3 пользователей
            'top_lists': top_lists,  # Передаем топ-3 списков
        }
    )


@login_required
@require_POST
def mark_watched(request):
    movie_id = request.POST.get('id')
    movie = get_object_or_404(Movie, id=movie_id)

    # Проверяем, был ли фильм уже просмотрен
    watched, created = Watched.objects.get_or_create(user=request.user, movie=movie)

    if created:
        # Если фильм был только что добавлен в просмотренные, увеличиваем счетчик
        movie.increment_views()

        # Начисляем 1 балл за просмотр
        PointsManager.add_points(request.user, PointsManager.POINTS_FOR_WATCHING, 'Просмотр фильма', target=movie)

        return JsonResponse({'status': 'added'})
    else:
        # Если фильм уже был просмотрен, удаляем отметку
        watched.delete()
        movie.decrement_views()

        # Снимаем 1 балл за отмену просмотра
        PointsManager.deduct_points(request.user, PointsManager.POINTS_FOR_WATCHING, 'Снятие просмотра фильма',
                                    target=movie)

        return JsonResponse({'status': 'removed'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
@require_POST
def mark_recently_watched(request):
    if request.method == 'POST':
        movie_id = request.POST.get('id')
        movie = get_object_or_404(Movie, id=movie_id)

        # Проверяем, был ли фильм уже просмотрен
        watched, created = Watched.objects.get_or_create(user=request.user, movie=movie)

        if created:
            # Если фильм был только что добавлен в просмотренные, увеличиваем счетчик
            movie.increment_views()
            # Начисляем 1 балл за просмотр
            PointsManager.add_points(request.user, PointsManager.POINTS_FOR_WATCHING, 'Просмотр фильма', target=movie)

            movie_url = request.build_absolute_uri(movie.get_absolute_url())
            create_action(request.user, 'недавно посмотрел', target=movie, movie_url=movie_url)
            return JsonResponse({'status': 'added'})
        else:
            # Если фильм уже был просмотрен, просто помечаем его как "недавно просмотренный"
            movie_url = request.build_absolute_uri(movie.get_absolute_url())
            create_action(request.user, 'недавно посмотрел', target=movie, movie_url=movie_url)
            return JsonResponse({'status': 'already_marked'})

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
    movie_id = request.POST.get('id')
    movie = get_object_or_404(Movie, id=movie_id)
    movie.add_like(request.user)  # Вызываем метод добавления лайка
    movie.refresh_from_db()  # Обновляем состояние объекта из базы данных
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

            # Проверяем, существует ли фильм
            if isinstance(cd['url'], dict) and 'exists' in cd['url']:
                existing_movie = cd['url']['movie']
                messages.info(request, f'Фильм {existing_movie.title} уже есть в базе данных.')
                return redirect(existing_movie.get_absolute_url())

            # Обработка жанров
            if 'genres' in cd:  # Проверяем, существует ли ключ 'genres'
                for genre in cd["genres"]:
                    if not Genre.objects.filter(name=genre).exists():
                        Genre.objects.create(name=genre)

            # Обработка стран
            if 'countries' in cd:  # Проверяем, существует ли ключ 'countries'
                for country in cd["countries"]:
                    if not Country.objects.filter(name=country).exists():
                        Country.objects.create(name=country)

            # Обработка режиссеров
            if 'directors' in cd:  # Проверяем, существует ли ключ 'directors'
                for director in cd["directors"]:
                    if not Director.objects.filter(staff_id=director["staff_id"]).exists():
                        Director.objects.create(name=director["name"], staff_id=director["staff_id"])

            # Обработка сценаристов
            if 'writers' in cd:  # Проверяем, существует ли ключ 'writers'
                for writer in cd["writers"]:
                    if not Writer.objects.filter(staff_id=writer["staff_id"]).exists():
                        Writer.objects.create(name=writer["name"], staff_id=writer["staff_id"])

            # Сохранение фильма
            new_movie = form.save(commit=True)  # Сохраняем объект в БД
            new_movie.user = request.user  # Устанавливаем пользователя
            new_movie.save()  # Сохраняем изменения
            PointsManager.add_points(request.user, PointsManager.POINTS_FOR_ADDING_MOVIE, 'Добавил фильм',
                                     target=new_movie)
            # Добавление связей
            for genre in cd.get("genres", []):  # Используем get с пустым списком по умолчанию
                genre_row = Genre.objects.get(name=genre)
                new_movie.genres.add(genre_row)
            for country in cd.get("countries", []):  # Используем get с пустым списком по умолчанию
                country_row = Country.objects.get(name=country)
                new_movie.countries.add(country_row)
            for director in cd.get("directors", []):  # Используем get с пустым списком по умолчанию
                director_row = Director.objects.get(staff_id=director["staff_id"])
                new_movie.directors.add(director_row)
            for writer in cd.get("writers", []):  # Используем get с пустым списком по умолчанию
                writer_row = Writer.objects.get(staff_id=writer["staff_id"])
                new_movie.writers.add(writer_row)

            messages.success(request, f'Фильм {new_movie.title} успешно добавлен')
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

    # Вычисляем соотношения
    like_ratio = movie.total_likes / movie.total_views if movie.total_views > 0 else 0
    dislike_ratio = movie.total_dislikes / movie.total_views if movie.total_views > 0 else 0

    if request.method == 'POST':
        form = CommentForm(data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.movie = movie
            comment.author = request.user
            comment.save()
            PointsManager.add_points(request.user, PointsManager.POINTS_FOR_COMMENT, 'Прокомментировал фильм', target=movie)
            movie_url = request.build_absolute_uri(movie.get_absolute_url())
            create_action(request.user, 'прокомментировал', target=movie, movie_url=movie_url)

            return redirect(movie.get_absolute_url())  # Перенаправление на страницу фильма
    else:
        form = CommentForm()  # Инициализация формы, если это не POST-запрос

    return render(request, 'movies/movie/detail.html', {
        'section': 'movies',
        'movie': movie,
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
    print("Полученные жанры:", genre_filter)  # Отладочный вывод

    # Удаляем пустые значения
    genre_filter = [genre for genre in genre_filter if genre]
    print("Жанры после удаления пустых значений:", genre_filter)  # Отладочный вывод

    # Преобразуем жанры в целые числа, игнорируя некорректные значения
    valid_genres = []
    for genre in genre_filter:
        try:
            # Пробуем преобразовать в целое число
            genre_id = int(genre)
            valid_genres.append(genre_id)
        except ValueError:
            # Игнорируем некорректные значения
            print(f"Игнорируем некорректное значение: {genre}")  # Отладочный вывод

    # Проверяем, есть ли валидные жанры
    if valid_genres:
        movies = movies.filter(genres__id__in=valid_genres).annotate(num_genres=Count('genres')).filter(
            num_genres=len(valid_genres)).distinct()
    else:
        print("Нет валидных жанров для фильтрации.")  # Отладочный вывод
    # Сортировка
    sort_by = request.GET.get('sort', 'created')  # По умолчанию сортируем по дате создания
    sort_order = request.GET.get('order', 'desc')  # Получаем порядок сортировки (asc или desc)

    if sort_by == 'year':
        movies = movies.order_by('year' if sort_order == 'asc' else '-year')
    elif sort_by == 'created':
        movies = movies.order_by('-created' if sort_order == 'desc' else 'created')
    elif sort_by == 'title':
        movies = movies.order_by('title' if sort_order == 'asc' else '-title')
    elif sort_by == 'watched':
        movies = movies.order_by('-total_views' if sort_order == 'desc' else 'total_views')
    elif sort_by == 'likes':
        movies = movies.order_by('-total_likes' if sort_order == 'desc' else 'total_likes')
    elif sort_by == 'dislikes':
        movies = movies.order_by('-total_dislikes' if sort_order == 'desc' else 'total_dislikes')
    elif sort_by == 'type':
        movies = movies.order_by('type_movie' if sort_order == 'asc' else '-type_movie')
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
        'selected_genres': genre_filter,  # Передаем выбранные жанры в шаблон
        'sort_by': sort_by,  # Передаем выбранный параметр сортировки в шаблон
        'sort_order': sort_order,  # Передаем порядок сортировки в шаблон
    })