import json
import logging
import telebot
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
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

def is_email_address(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def handle_kinopoisk_url(chat_id, url):
    form = MovieCreateForm(data={'url': url}, source='telegram')
    user = User.objects.get(profile__telegram_user_id=chat_id)

    if form.is_valid():
        cd = form.cleaned_data
        logger.info(f"Cleaned data from form: {cd}")

        # Проверка на существование фильма
        if isinstance(cd['url'], dict) and 'exists' in cd['url']:
            existing_movie = cd['url']['movie']
            movie_list_url = f"{config('SITE_URL')}/movies/?kinopoisk_id={existing_movie.kinopoisk_id}"
            bot.send_message(chat_id, f"Фильм с ID {existing_movie.kinopoisk_id} уже был добавлен ранее.\n"
                                       f"По ссылке Вы можете проставить отметки фильму: {movie_list_url}",
                             parse_mode='HTML')
            return

        # Проверка на наличие необходимых данных
        if not cd.get("title") or not cd.get("kinopoisk_id"):
            bot.send_message(chat_id, "Ошибка: недостающие данные для добавления фильма.", parse_mode='HTML')
            return

        # Создаем новый объект фильма
        new_movie = form.save(commit=False)  # Сохраняем объект, но не в БД
        new_movie.user = user  # Устанавливаем пользователя
        new_movie.title = cd["title"]
        new_movie.title_original = cd.get("title_original", "")
        new_movie.year = cd.get("year", 0)
        new_movie.duration = cd.get("duration", 0)
        new_movie.kinopoisk_id = cd["kinopoisk_id"]
        new_movie.kinopoisk_url = cd["kinopoisk_url"]
        new_movie.url = cd.get("url", "")
        new_movie.description = cd.get("description", "")
        new_movie.movie_json = cd.get("movie_data", {})
        new_movie.movie_staff_json = cd.get("movie_staff_data", {})
        new_movie.type_movie = cd.get("type_movie", "FILM")

        # Сохраняем новый фильм в базе данных
        new_movie.save()

        # Добавление жанров, стран, режиссеров и сценаристов
        for genre in cd.get("genres", []):
            genre_row, created = Genre.objects.get_or_create(name=genre)
            new_movie.genres.add(genre_row)
        for country in cd.get("countries", []):
            country_row, created = Country.objects.get_or_create(name=country)
            new_movie.countries.add(country_row)
        for director in cd.get("directors", []):
            director_row, created = Director.objects.get_or_create(staff_id=director["staff_id"], defaults={'name': director["name"]})
            new_movie.directors.add(director_row)
        for writer in cd.get("writers", []):
            writer_row, created = Writer.objects.get_or_create(staff_id=writer["staff_id"], defaults={'name': writer["name"]})
            new_movie.writers.add(writer_row)

        movie_url = f"{config('SITE_URL')}{new_movie.get_absolute_url()}"
        movie_list_url = f"{config('SITE_URL')}/movies/?kinopoisk_id={new_movie.kinopoisk_id}"
        create_action(user, 'добавил', target=new_movie, movie_url=movie_url)
        bot.send_message(chat_id, f"Фильм 🎬<b>{new_movie.title}</b> успешно добавлен!\n"
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

        # Проверяем, является ли сообщение email-адресом
        if is_email_address(command):
            handle_email(chat_id, command)  # Обрабатываем email
            return

        # Проверяем, является ли сообщение URL Кинопоиска
        kinopoisk_url = is_kinopoisk_url(command)
        if kinopoisk_url:
            handle_kinopoisk_url(chat_id, kinopoisk_url)  # Обрабатываем URL Кинопоиска
            return

        # Обработка команд
        if command.startswith('/start'):
            start(chat_id)
        elif command.startswith('/connect'):
            connect(chat_id)
        else:
            bot.send_message(chat_id, "Неизвестная команда. Пожалуйста, используйте /start или /connect.")

def handle_email(chat_id, email):
    try:
        user = User.objects.get(email=email)
        profile, created = Profile.objects.get_or_create(telegram_user_id=str(chat_id))  # Получаем или создаем профиль
        if profile.user:  # Проверяем, есть ли уже привязка
            bot.send_message(chat_id, 'По данному email уже выполнена привязка к аккаунту.')
            return
        profile.user = user  # Связываем профиль с пользователем
        profile.telegram_connected = True
        profile.save()
        bot.send_message(chat_id, 'Ваш аккаунт успешно связан с Telegram!')
    except User.DoesNotExist:
        bot.send_message(chat_id, 'Такого email нет в базе данных. Пожалуйста, пройдите регистрацию.')
    except Exception as e:
        logger.error(f"Error in handle_email: {e}")
        bot.send_message(chat_id, 'Произошла ошибка при связывании аккаунта. Пожалуйста, попробуйте еще раз.')

def start(chat_id):
    bot.send_message(chat_id, 'Привет! Используйте команду /connect для связывания вашего аккаунта.')