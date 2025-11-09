from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages  # Импортируем для работы с сообщениями
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import logging
from datetime import timedelta
from .models import Contact, PointsHistory
from actions.utils import create_action
from actions.models import Action
from movies.models import Movie, Watched, WishList
from lists.models import MovieList
from telegram_bot.notifications import send_new_profile_notification
from decouple import config


from .forms import (
    LoginForm,
    ProfileEditForm,
    UserEditForm,
    UserRegistrationForm,
)
from .models import Profile

logger = logging.getLogger(__name__)
User = get_user_model()


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(
                request,
                username=cd['username'],
                password=cd['password'],
            )
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Authenticated successfully')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})

@login_required
def dashboard(request):
    # Получаем количество просмотренных фильмов
    watched_count = Watched.objects.filter(user=request.user).count()
    # Получаем количество понравившихся фильмов
    liked_count = request.user.movies_like.count()
    # Получаем количество непонравившихся фильмов
    disliked_count = request.user.movies_dislike.count()
    # Получаем количество добавленных фильмов
    added_movies_count = request.user.movies_add.count()
    # Получаем количество фильмов в вишлисте
    wishlist_count = WishList.objects.filter(user=request.user).count()

    # Фильтрация действий
    filter_option = request.GET.get('filter', 'all')
    if filter_option == 'day':
        start_date = timezone.now() - timedelta(days=1)
    elif filter_option == 'week':
        start_date = timezone.now() - timedelta(weeks=1)
    elif filter_option == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif filter_option == 'year':
        start_date = timezone.now() - timedelta(days=365)
    else:
        start_date = None

    # Фильтрация действий
    actions = Action.objects.filter(user=request.user)
    if start_date:
        actions = actions.filter(created__gte=start_date)

    # Пагинация для действий
    paginator = Paginator(actions.order_by('-created'), 10)  # 10 действий на страницу
    page_number = request.GET.get('page')
    actions_page = paginator.get_page(page_number)

    # Фильтрация комментариев
    comments = request.user.comments.all()
    if start_date:
        comments = comments.filter(created_on__gte=start_date)

    # Пагинация для комментариев
    comments_paginator = Paginator(comments.order_by('-created_on'), 10)
    comments_page_number = request.GET.get('comments_page')
    comments_page = comments_paginator.get_page(comments_page_number)

    # Фильтрация истории начислений
    points_history = PointsHistory.objects.filter(user=request.user)
    if start_date:
        points_history = points_history.filter(created_at__gte=start_date)

    # Пагинация для истории начислений
    points_paginator = Paginator(points_history.order_by('-created_at'), 10)
    points_page_number = request.GET.get('points_page')
    points_page = points_paginator.get_page(points_page_number)

    # Получаем всех пользователей и сортируем по баллам
    users = Profile.objects.select_related('user').order_by('-points')
    user_position = list(users).index(request.user.profile) + 1  # Позиция начинается с 1

    # Определяем активную вкладку
    active_tab = request.GET.get('tab', 'activity')  # По умолчанию активна вкладка "Активность"

    # Получаем списки пользователя
    movie_lists = MovieList.objects.filter(user=request.user)

    # Передаем сообщения в контекст
    return render(
        request,
        # 'account/dashboard.html',
        'account/dashboard-migration.html',
        {
            'section': 'dashboard',
            'actions': actions_page,
            'comments': comments_page,
            'points_history': points_page,
            'bot_url': config('BOT_URL'),
            'watched_count': watched_count,
            'liked_count': liked_count,
            'disliked_count': disliked_count,
            'added_movies_count': added_movies_count,
            'wishlist_count': wishlist_count,
            'user_position': user_position,
            'filter_option': filter_option,  # Передаем выбранный фильтр
            'active_tab': active_tab,  # Передаем активную вкладку
            'movie_lists': movie_lists,  # Передаем списки пользователя
            'messages': messages.get_messages(request),  # Передаем сообщения
        }
    )
@login_required
def user_movie_list(request, username):
    user = get_object_or_404(User, username=username, is_active=True)

    # Получаем все фильмы по умолчанию
    watched_movies = Movie.objects.filter(watched__user=user)
    liked_movies = Movie.objects.filter(users_like=user)
    disliked_movies = Movie.objects.filter(users_dislike=user)
    wishlist_movies = Movie.objects.filter(wishlist__user=user)
    added_movies = Movie.objects.filter(user=user)  # Фильмы, добавленные пользователем
    wishlist_movies_curuser = WishList.objects.filter(user=request.user).values_list('movie_id', flat=True)
    watched_movies_curuser = Watched.objects.filter(user=request.user).values_list('movie_id', flat=True)
    # Фильтрация по вкладкам
    filter_type = request.GET.get('filter', 'all')  # Получаем тип фильтра из параметров запроса

    # Определяем, какие фильмы показывать в зависимости от фильтра
    if filter_type == 'watched':
        movies = watched_movies
    elif filter_type == 'liked':
        movies = liked_movies
    elif filter_type == 'disliked':
        movies = disliked_movies
    elif filter_type == 'wishlist':
        movies = wishlist_movies
    elif filter_type == 'added':  # Добавляем новый фильтр
        movies = added_movies
    else:
        movies = Movie.objects.none()  # Если фильтр не распознан, не показываем фильмы

    # Фильтрация по названию
    title_filter = request.GET.get('title', '')
    if title_filter:
        movies = movies.filter(title__icontains=title_filter) | movies.filter(title_original__icontains=title_filter)

    # Пагинация
    paginator = Paginator(movies, 10)  # Показывать 10 фильмов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'movies/movie/user_movie_list.html', {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'title_filter': title_filter,
        'user': user,  # Передаем пользователя, чьи фильмы мы отображаем
        'watched_movies': watched_movies,
        'liked_movies': liked_movies,
        'disliked_movies': disliked_movies,
        'wishlist_movies': wishlist_movies,
        'added_movies': added_movies,  # Передаем добавленные фильмы
        'watched_movies_curuser': watched_movies_curuser,
        'wishlist_movies_curuser': wishlist_movies_curuser,
    })

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            # Set the chosen password
            new_user.set_password(user_form.cleaned_data['password'])
            # Save the User object
            new_user.save()
            # Create the user profile
            Profile.objects.create(user=new_user)
            create_action(new_user, 'зарегистрировался')
            send_new_profile_notification(new_user.username)
            return render(
                request,
                'account/register_done.html',
                {'new_user': new_user},
            )
    else:
        user_form = UserRegistrationForm()
    return render(
        request,
        'account/register.html',
        {'user_form': user_form}
    )


@login_required
def edit(request):
    # Получаем или создаем профиль для пользователя
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserEditForm(
            instance=request.user,
            data=request.POST
        )
        profile_form = ProfileEditForm(
            instance=profile,
            data=request.POST,
            files=request.FILES,
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(
                request,
                'Профиль успешно изменен'
            )
            return redirect('dashboard')  # Перенаправление после успешного обновления
        else:
            messages.error(request, 'Ошибка при обновлении профиля')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)

    return render(
        request,
        'account/edit.html',
        {
            'user_form': user_form,
            'profile_form': profile_form
        },
    )


@login_required
def user_list(request):
    # Получаем всех активных пользователей, кроме текущего
    users = User.objects.filter(is_active=True).exclude(is_superuser=True)
    return render(
        request,
        # 'account/user/list.html',
                  'account/user/list-migration.html',
        {
        'section': 'people',
        'users': users
    })



@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)

    # Получаем количество просмотренных фильмов
    watched_count = Watched.objects.filter(user=user).count()
    # Получаем количество понравившихся фильмов
    liked_count = user.movies_like.count()
    # Получаем количество непонравившихся фильмов
    disliked_count = user.movies_dislike.filter(user=user).count()
    # Получаем количество фильмов в вишлисте
    wishlist_count = WishList.objects.filter(user=user).count()
    # Получаем количество добавленных фильмов (если у вас есть такая связь)
    added_count = Movie.objects.filter(
        user=user).count()  # Предполагается, что у вас есть связь с добавленными фильмами

    # Получаем недавние действия пользователя
    actions = user.actions.all().order_by('-created')  # Предполагается, что у вас есть связь с действиями
    # Пагинация для действий
    actions_paginator = Paginator(actions, 10)  # 10 действий на страницу
    actions_page_number = request.GET.get('actions_page')
    actions_page = actions_paginator.get_page(actions_page_number)

    # Получаем комментарии пользователя
    comments = user.comments.all().order_by('-created_on')  # Предполагается, что у вас есть связь с комментариями
    # Пагинация для комментариев
    comments_paginator = Paginator(comments, 10)  # 10 комментариев на страницу
    comments_page_number = request.GET.get('comments_page')
    comments_page = comments_paginator.get_page(comments_page_number)

    # Вычисляем совместимость
    current_user_liked_movies = request.user.movies_like.values_list('id', flat=True)
    user_liked_movies = user.movies_like.values_list('id', flat=True)
    # Находим количество совпадений
    common_movies_count = user.movies_like.filter(id__in=current_user_liked_movies).count()
    # Вычисляем процент совместимости
    compatibility_score = (common_movies_count / max(liked_count, 1)) * 100  # Избегаем деления на ноль
    # Определяем активную вкладку
    active_tab = request.GET.get('tab', 'aboutme')  # По умолчанию активна вкладка "О пользователе"

    return render(
        request,
        # 'account/user/detail.html',
        'account/user/detail-migration.html',
        {
        'section': 'people',
        'user': user,
        'watched_count': watched_count,
        'liked_count': liked_count,
        'disliked_count': disliked_count,
        'wishlist_count': wishlist_count,  # Добавлено количество фильмов в вишлисте
        'added_count': added_count,  # Добавлено количество добавленных фильмов
        'actions': actions_page,  # Передаем пагинированные действия в шаблон
        'comments': comments_page,  # Передаем пагинированные комментарии в шаблон
        'common_movies_count': common_movies_count,  # Добавлено количество общих фильмов
        'compatibility_score': round(compatibility_score, 2),  # Округляем до 2 знаков после запятой
        'active_tab': active_tab,  # Передаем активную вкладку
    })



@require_POST
@login_required
def user_follow(request):
    try:
        # Загружаем данные из тела запроса
        data = json.loads(request.body)
        user_id = data.get('id')
        action = data.get('action')

        logger.info(f"Received follow request: user_id={user_id}, action={action}")

        if user_id and action:
            try:
                user = User.objects.get(id=user_id)
                if action == 'follow':
                    # Создаем связь "подписка"
                    Contact.objects.get_or_create(
                        user_from=request.user,
                        user_to=user
                    )
                    create_action(request.user, 'подписался', user)
                    return JsonResponse({'status': 'ok'})
                elif action == 'unfollow':
                    # Удаляем связь "подписка"
                    contact = Contact.objects.filter(user_from=request.user, user_to=user)
                    if contact.exists():
                        contact.delete()
                        create_action(request.user, 'отписался', user)
                        return JsonResponse({'status': 'ok'})
                    else:
                        return JsonResponse({'status': 'error', 'message': 'Not following this user.'})
                return JsonResponse({'status': 'error', 'message': 'Invalid action.'})
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'User  does not exist.'})

        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'})


@login_required
def user_followers_list(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        followers = user.followers.all()  # Получаем всех подписчиков
        followers_data = [{'id': follower.id, 'full_name': follower.get_full_name()} for follower in followers]

        return JsonResponse({'followers': followers_data})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)



@login_required
def user_ranking(request):
    # Получаем всех пользователей и сортируем по баллам
    users = Profile.objects.select_related('user').order_by('-points')

    # Определяем позицию текущего пользователя
    user_position = list(users).index(request.user.profile) + 1  # Позиция начинается с 1

    return render(request, 'account/user_ranking.html', {
        'users': users,
        'user_position': user_position,
    })