# lists/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from .models import MovieList
from movies.models import Movie, Watched, WishList
from django.core.paginator import Paginator
from account.points_manager import PointsManager
from django.db.models import Count
from actions.models import Action
from actions.utils import create_action

@login_required
def create_movie_list(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        movie_list = MovieList.objects.create(title=title, user=request.user)
        PointsManager.add_points(request.user, PointsManager.POINTS_FOR_CREATING_LIST, 'Создание списка', target=movie_list)
        return redirect('lists:add_movies_to_list', list_id=movie_list.id)
    return render(request, 'lists/create_movie_list.html')

@login_required
def movie_list_detail(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id)
    movies = movie_list.movies.all().order_by('-year')
    wishlist_movies = WishList.objects.filter(user=request.user).values_list('movie_id', flat=True)
    watched_movies = Watched.objects.filter(user=request.user).values_list('movie_id', flat=True)

    return render(request, 'lists/movie_list_detail.html', {
        'movie_list': movie_list,
        'movies': movies,
        'watched_movies': watched_movies,
        'wishlist_movies': wishlist_movies,
        'can_edit': request.user == movie_list.user,
        'can_like': request.user != movie_list.user,  # Добавляем переменную для проверки возможности лайка
    })


# lists/views.py
@login_required
def like_movie_list(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id)

    if request.user in movie_list.users_like.all():
        # Если пользователь уже лайкнул, убираем лайк
        movie_list.users_like.remove(request.user)
        # Снимаем 3 балла у создателя списка
        PointsManager.deduct_points(movie_list.user, PointsManager.POINTS_FOR_LIKING_LIST, 'Убрал лайк с списка',
                                    target=movie_list)
        movie_list.add_points(-3)  # Снимаем баллы со списка
    else:
        # Если пользователь не лайкнул, добавляем лайк
        movie_list.users_like.add(request.user)
        # Начисляем 3 балла создателю списка
        PointsManager.add_points(movie_list.user, PointsManager.POINTS_FOR_LIKING_LIST, 'Поставил лайк на список',
                                 target=movie_list)
        movie_list.add_points(3)  # Начисляем баллы со списка

    return redirect('lists:movie_list_detail', list_id=list_id)


@login_required
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
        return render(request, 'lists/add_movies_to_list.html', {
            'movie_list': movie_list,
            'page_obj': page_obj,
            'search_query': search_query,
        })

    return render(request, 'lists/add_movies_to_list.html', {
        'movie_list': movie_list,
        'page_obj': page_obj,
        'search_query': search_query,
    })

def view_movie_list(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id)

    if request.method == 'POST':
        if 'save_list' in request.POST:
            # Логика для сохранения списка (если это необходимо)
            return redirect('lists:movie_list_detail', list_id=list_id)  # Перенаправляем на страницу созданного списка
        elif 'clear_list' in request.POST:
            # Очистка списка
            movie_list.movies.clear()  # Удаляем все фильмы из списка
            return redirect('lists:add_movies_to_list', list_id=movie_list.id)  # Перенаправляем на страницу добавления фильмов

    return render(request, 'lists/view_movie_list.html', {'movie_list': movie_list})

@login_required
def users_movie_lists(request):
    # Получаем все списки фильмов, созданные всеми пользователями, и аннотируем количество лайков
    movie_lists = MovieList.objects.prefetch_related('movies', 'user').annotate(likes_count=Count('users_like')).order_by('-likes_count')

    # Получаем список ID фильмов, просмотренных текущим пользователем
    watched_movies = Watched.objects.filter(user=request.user).values_list('movie_id', flat=True)

    # Подсчитываем количество просмотренных фильмов для каждого списка
    for movie_list in movie_lists:
        movie_list.watched_count = sum(1 for movie in movie_list.movies.all() if movie.id in watched_movies)
        movie_list.total_count = movie_list.movies.count()
        movie_list.watched_percentage = (movie_list.watched_count / movie_list.total_count * 100) if movie_list.total_count > 0 else 0

    return render(request, 'lists/users_movie_lists.html', {
        'movie_lists': movie_lists,
    })