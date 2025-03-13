from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Contact, PointsHistory
import json
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from actions.utils import create_action
from actions.models import Action
from movies.models import Movie, Watched, WishList
from telegram_bot.views import send_new_profile_notification


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
    added_movies_count = request.user.movies_add.count()  # Получаем количество добавленных фильмов
    # Получаем количество фильмов в вишлисте
    wishlist_count = WishList.objects.filter(user=request.user).count()  # Получаем количество фильмов в вишлисте
    # Получаем комментарии пользователя
    comments = request.user.comments.all()  # Предполагается, что у вас есть связь между пользователем и комментариями
    # Получаем действия текущего пользователя
    actions = Action.objects.filter(user=request.user).select_related('user', 'user__profile').prefetch_related('target')[:10]

    # Получаем историю начислений баллов
    points_history = PointsHistory.objects.filter(user=request.user).order_by('-created_at')  # Сортируем по дате

    # Получаем всех пользователей и сортируем по баллам
    users = Profile.objects.select_related('user').order_by('-points')
    # Определяем позицию текущего пользователя
    user_position = list(users).index(request.user.profile) + 1  # Позиция начинается с 1

    return render(
        request,
        'account/dashboard.html',
        {
            'section': 'dashboard',
            'actions': actions,
            'watched_count': watched_count,
            'liked_count': liked_count,
            'disliked_count': disliked_count,
            'added_movies_count': added_movies_count,  # Добавлено количество добавленных фильмов
            'wishlist_count': wishlist_count,  # Добавлено количество фильмов в вишлисте
            'comments': comments,
            'points_history': points_history,  # Передаем историю начислений
            'user_position': user_position,  # Передаем позицию пользователя
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
    users = User.objects.filter(is_active=True)
    return render(request, 'account/user/list.html', {
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
    added_count = Movie.objects.filter(user=user).count()  # Предполагается, что у вас есть связь с добавленными фильмами
    # Получаем недавние действия пользователя (например, лайки, дизлайки и т.д.)
    actions = user.actions.all()[:10]  # Предполагается, что у вас есть связь с действиями
    # Получаем комментарии пользователя
    comments = user.comments.all()  # Предполагается, что у вас есть связь с комментариями
    # Вычисляем совместимость
    current_user_liked_movies = request.user.movies_like.values_list('id', flat=True)
    user_liked_movies = user.movies_like.values_list('id', flat=True)
    # Находим количество совпадений
    common_movies_count = user.movies_like.filter(id__in=current_user_liked_movies).count()
    # Вычисляем процент совместимости
    compatibility_score = (common_movies_count / max(liked_count, 1)) * 100  # Избегаем деления на ноль

    return render(request, 'account/user/detail.html', {
        'section': 'people',
        'user': user,
        'watched_count': watched_count,
        'liked_count': liked_count,
        'disliked_count': disliked_count,
        'wishlist_count': wishlist_count,  # Добавлено количество фильмов в вишлисте
        'added_count': added_count,  # Добавлено количество добавленных фильмов
        'actions': actions,
        'comments': comments,  # Передаем комментарии в шаблон
        'common_movies_count': common_movies_count,  # Добавлено количество общих фильмов
        'compatibility_score': round(compatibility_score, 2),  # Округляем до 2 знаков после запятой
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