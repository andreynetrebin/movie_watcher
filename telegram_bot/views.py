import json
import logging
import telebot
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.urls import reverse
from movies.models import Movie, Genre, Country, Director, Writer, Watched, WishList
from account.models import Profile
from actions.utils import create_action
from decouple import config
from movies.forms import MovieCreateForm  # Импортируйте вашу форму
import re

User  = get_user_model()
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(config('TELEGRAM_BOT_TOKEN'))

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        update = json.loads(request.body)
        logger.info(f"Received update: {update}")
        try:
            # Обработка обновления
            process_update(update)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

def is_kinopoisk_url(url):
    pattern = r'https://www\.kinopoisk\.ru/(film|series)/(\d+)/'
    match = re.search(pattern, url)
    if match:
        return match.group(0)  # Возвращаем полный URL, если он соответствует шаблону
    return None  # Возвращаем None, если URL не соответствует шаблону



def handle_kinopoisk_url(chat_id, url):
    form = MovieCreateForm(data={'url': url}, source='telegram')
    user = User.objects.get(profile__telegram_user_id=chat_id)
    if form.is_valid():
        cd = form.cleaned_data
        logger.info(f"Cleaned data from form: {cd}")
        if 'exists' in cd['url']:
            kinopoisk_id = cd['url']['kinopoisk_id']
            movie_list_url = f"{config('SITE_URL')}/movies/?kinopoisk_id={kinopoisk_id}"
            bot.send_message(chat_id, f"Фильм с ID {kinopoisk_id} уже был добавлен ранее.\n"
                   f"По ссылке Вы можете проставить отметки фильму: {movie_list_url}",
                     parse_mode='HTML')
            return
        new_movie = form.save(commit=False)
        new_movie.user = user
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
        new_movie.type_movie = cd["type_movie"]
        new_movie.save()

        # Добавление жанров, стран, режиссеров и сценаристов
        for genre in cd["genres"]:
            genre_row, created = Genre.objects.get_or_create(name=genre)
            new_movie.genres.add(genre_row)
        for country in cd["countries"]:
            country_row, created = Country.objects.get_or_create(name=country)
            new_movie.countries.add(country_row)
        for director in cd["directors"]:
            director_row, created = Director.objects.get_or_create(staff_id=director["staff_id"], defaults={'name': director["name"]})
            new_movie.directors.add(director_row)
        for writer in cd["writers"]:
            writer_row, created = Writer.objects.get_or_create(staff_id=writer["staff_id"], defaults={'name': writer["name"]})
            new_movie.writers.add(writer_row)

        movie_url = f"{config('SITE_URL')}{new_movie.get_absolute_url()}"
        movie_list_url = f"{config('SITE_URL')}/movies/?kinopoisk_id={new_movie.kinopoisk_id}"
        create_action(user, 'добавил', target=new_movie, movie_url=movie_url)

        # Отправляем сообщение с вариантами действий
        bot.send_message(chat_id, f"Фильм 🎬<b>{new_movie.title}</b> успешно добавлен!\n"
                                  f"Ссылка на фильм: {movie_url}\n"
                                  f"По ссылке Вы можете проставить отметки фильму: {movie_list_url}",
                                  parse_mode='HTML')

    else:
        # Если форма не валидна, отправляем сообщение с ошибкой
        for error in form.errors.values():
            bot.send_message(chat_id, f"Ошибка: {error[0]}", parse_mode='HTML')


def process_update(update):
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        command = message.get('text', '')

        # Получаем профиль пользователя или создаем новый, если его нет
        profile, created = Profile.objects.get_or_create(telegram_user_id=str(chat_id))

        if command.startswith('/start'):
            start(chat_id)
        elif command.startswith('/connect'):
            connect(chat_id)
        elif profile.state == 'waiting_for_email':
            handle_email(chat_id, command)  # Обрабатываем email
            profile.state = 'none'  # Сбрасываем состояние после обработки
            profile.save()
        else:  # Если профиль существует, обрабатываем URL Кинопоиска
            kinopoisk_url = is_kinopoisk_url(command)
            if kinopoisk_url:
                handle_kinopoisk_url(chat_id, kinopoisk_url)  # Обрабатываем URL Кинопоиска
            else:
                bot.send_message(chat_id,
                                 "В переданном тексте не распознан соответствующий формату URL из Кинопоиска. "
                                 "Формат URL: https://www.kinopoisk.ru/(film|series)/(\d+)/",
                                 parse_mode='HTML')
def start(chat_id):
    bot.send_message(chat_id, 'Привет! Используйте команду /connect для связывания вашего аккаунта.')

def connect(chat_id):
    bot.send_message(chat_id, 'Пожалуйста, введите ваш email для связывания аккаунта:')
    # Устанавливаем состояние ожидания email
    profile, created = Profile.objects.get_or_create(telegram_user_id=str(chat_id))
    profile.state = 'waiting_for_email'
    profile.save()
def handle_email(chat_id, email):
    try:
        user = User.objects.get(email=email)
        profile = Profile.objects.get(telegram_user_id=str(chat_id))  # Получаем профиль по telegram_user_id
        profile.user = user  # Связываем профиль с пользователем
        profile.telegram_connected = True
        profile.state = 'none'  # Сбрасываем состояние
        profile.save()
        bot.send_message(chat_id, 'Ваш аккаунт успешно связан с Telegram!')
    except User.DoesNotExist:
        bot.send_message(chat_id, 'Такого email нет в базе данных. Пожалуйста, пройдите регистрацию.')
    except Profile.DoesNotExist:
        bot.send_message(chat_id, 'Профиль не найден. Пожалуйста, выполните команду /connect.')
def send_version_notification(version_number, release_date, changes):
    # Эмодзи для сообщения
    emoji = "📢"  # Вы можете выбрать любой эмодзи, который вам нравится

    # Формируем сообщение в Markdown
    message = (
        f"{emoji} *Выпущена версия:* {version_number}\n"
        f"*Дата:* {release_date}\n"
        f"*Изменения:*\n{changes}\n\n"
        f"🔗 [Полный перечень изменений]({config('SITE_URL')}/versioning/changelog/)"
    )

    # Получаем всех пользователей, которые связали свои аккаунты с Telegram
    profiles = Profile.objects.filter(telegram_connected=True)
    for profile in profiles:
        chat_id = profile.telegram_user_id
        bot.send_message(chat_id, message, parse_mode='Markdown')


def send_movie_action_notification(movie, movie_url, action_user, action):
    # Получаем всех подписчиков пользователя, который совершил действие
    subscribers = action_user.followers.all()  # Получаем всех подписчиков
    logger.info(f"Found {subscribers.count()} subscribers for {action_user.username}")

    # Список действий с соответствующими хештегами
    actions = [
        {'action': '📋 добавил в "Буду смотреть"', 'hashtag': 'Будет_смотреть📋'},
        {'action': '🍿 недавно посмотрел', 'hashtag': 'Недавно_просмотрен🍿'},
        {'action': '👍 понравился', 'hashtag': 'Понравился👍'},
        {'action': '👎 не понравился', 'hashtag': 'Не_понравился👎'},
        {'action': '🎬 добавил', 'hashtag': 'Добавлен🎬'},
        {'action': '✏️ прокомментировал', 'hashtag': 'Прокомментирован✏️'},
    ]
    # Находим хештег для действия
    hashtag = None
    for act in actions:
        if act['action'] == action:
            hashtag = act['hashtag']
            break

    for subscriber in subscribers:
        # Получаем профиль подписчика
        subscriber_profile = Profile.objects.get(user=subscriber)
        chat_id = subscriber_profile.telegram_user_id

        if chat_id:  # Проверяем, что у подписчика есть Telegram ID
            message = (
                f"<b>{action_user.username}</b> {action} фильм <b>{movie.title}</b>.\n"
                f"Ссылка на Кинопоиск: {movie.kinopoisk_url}\n"
                f"Ссылка на страницу фильма: {movie_url}\n\n\n"
                f"#{movie.title.replace(' ', '_')}🎥\n"  # Хештег с названием фильма
                f"#{action_user.username}😊\n"  # Хештег с именем пользователя
                f"#{hashtag}" if hashtag else ""  # Хештег действия, если найден
            )
            try:
                bot.send_message(chat_id, message, parse_mode='HTML')
                logger.info(f"Message sent to {subscriber.username} ({chat_id})")
            except Exception as e:
                logger.error(f"Error sending message to {chat_id}: {e}")
        else:
            logger.warning(f"No Telegram ID for subscriber: {subscriber.username}")



def send_new_profile_notification(username):
    # Получаем всех пользователей, которые связали свои аккаунты с Telegram
    profiles = Profile.objects.filter(telegram_connected=True)
    for profile in profiles:
        chat_id = profile.telegram_user_id
        # Формируем ссылку на профиль пользователя
        profile_url = reverse('user_detail', kwargs={'username': username})
        # Обрезаем один символ справа от SITE_URL
        site_url = config('SITE_URL')[:-1]  # Обрезаем последний символ
        message = (
            f"Зарегистрировался новый пользователь - <b>{username}</b>\n"
            f"Ссылка на профиль🤙: {site_url}{profile_url}\n\n"
            f"#Новичок🥸"
                    )
        bot.send_message(chat_id, message, parse_mode='HTML')

