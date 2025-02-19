from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Contact
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from actions.utils import create_action
from actions.models import Action
from movies.models import Movie, Watched
from telegram_bot.views import send_newuser_registration_notification


from .forms import (
    LoginForm,
    ProfileEditForm,
    UserEditForm,
    UserRegistrationForm,
)
from .models import Profile


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

    # Получаем комментарии пользователя
    comments = request.user.comments.all()  # Предполагается, что у вас есть связь между пользователем и комментариями

    # Получаем действия текущего пользователя
    actions = Action.objects.filter(user=request.user).select_related('user', 'user__profile').prefetch_related('target')[:10]

    return render(
        request,
        'account/dashboard.html',
        {
            'section': 'dashboard',
            'actions': actions,
            'watched_count': watched_count,
            'liked_count': liked_count,
            'disliked_count': disliked_count,
            'comments': comments,
        }
    )
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
            create_action(new_user, 'has created an account')
            send_newuser_registration_notification(new_user.username)
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


from django.shortcuts import get_object_or_404

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
            return redirect('account:profile')  # Перенаправление после успешного обновления
        else:
            messages.error(request, 'Error updating your profile')
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
    users = User.objects.filter(is_active=True)
    return render(request,
    'account/user/list.html',
    {'section': 'people',
    'users': users})

@login_required
def user_detail(request, username):
    user = get_object_or_404(User,
    username=username,
    is_active=True)
    return render(request,
    'account/user/detail.html',
    {'section': 'people',
    'user': user})

@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(
                    user_from=request.user,
                    user_to=user)
                create_action(request.user, 'is following', user)
            else:
                Contact.objects.filter(user_from=request.user,
                user_to=user).delete()
            return JsonResponse({'status':'ok'})
        except User.DoesNotExist:
            return JsonResponse({'status':'error'})
    return JsonResponse({'status':'error'})