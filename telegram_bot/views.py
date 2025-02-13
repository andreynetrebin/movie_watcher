import json
import logging
import telebot
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from account.models import Profile
from decouple import config

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


def send_movie_action_notification(movie, movie_url, action_user, action):
    # Получаем всех пользователей, которые связали свои аккаунты с Telegram
    profiles = Profile.objects.filter(telegram_connected=True)
    for profile in profiles:
        chat_id = profile.telegram_user_id
        if chat_id == "544324614":
            message = (
                f"<b>{action_user.username}</b> {action} фильм <b>{movie.title}</b>.\n"
                f"Ссылка на Кинопоиск: {movie.kinopoisk_url}\n"
                f"Ссылка на страницу фильма: {movie_url}"
            )
            bot.send_message(chat_id, message, parse_mode='HTML')

def send_newuser_registration_notification(username):
    # Получаем всех пользователей, которые связали свои аккаунты с Telegram
    profiles = Profile.objects.filter(telegram_connected=True)
    for profile in profiles:
        chat_id = profile.telegram_user_id
        if chat_id == "544324614":
            message = (
                f"Зарегистрировался новый пользователь - <b>{username}</b>"
            )
            bot.send_message(chat_id, message, parse_mode='HTML')


# def send_movie_action_notification(request, movie, action_user, action):
#     # Получаем всех пользователей, которые связали свои аккаунты с Telegram
#     profiles = Profile.objects.filter(telegram_connected=True)
#     for profile in profiles:
#         chat_id = profile.telegram_user_id
#         message = (
#             f"<b>{action_user.username}</b> {action} фильм <b>{movie.title}</b>.\n"
#             f"Ссылка на Кинопоиск: {movie.kinopoisk_url}\n"
#             f"Ссылка на страницу фильма: {request.build_absolute_uri(movie.get_absolute_url())}"
#         )
#         bot.send_message(chat_id, message, parse_mode='HTML')
#
#
# def send_movie_notification(request, movie, action_user, action):
#     # Получаем всех пользователей, которые связали свои аккаунты с Telegram
#     profiles = Profile.objects.filter(telegram_connected=True)
#     for profile in profiles:
#         chat_id = profile.telegram_user_id
#         emoji = '👍' if action == 'liked' else '👎'
#         message = (
#             f"<b>{action_user.username}</b> {emoji} "
#             f"фильм <b>{movie.title}</b>.\n"
#             f"Ссылка на Кинопоиск: {movie.kinopoisk_url}\n"
#             f"Ссылка на страницу фильма: {request.build_absolute_uri(movie.get_absolute_url())}"
#         )
#         bot.send_message(chat_id, message, parse_mode='HTML')

def process_update(update):
    # Обработка обновления без блокировок
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        command = message.get('text', '')

        if command.startswith('/start'):
            start(chat_id)
        elif command.startswith('/connect'):
            connect(chat_id)
        else:
            handle_email(chat_id, command)

def start(chat_id):
    bot.send_message(chat_id, 'Привет! Используйте команду /connect для связывания вашего аккаунта.')

def connect(chat_id):
    bot.send_message(chat_id, 'Пожалуйста, введите ваш email для связывания аккаунта:')

def handle_email(chat_id, email):
    try:
        user = User.objects.get(email=email)
        profile = user.profile
        profile.telegram_connected = True
        profile.telegram_user_id = str(chat_id)
        profile.save()
        bot.send_message(chat_id, 'Ваш аккаунт успешно связан с Telegram!')
    except User.DoesNotExist:
        bot.send_message(chat_id, 'Такого email нет в базе данных. Пожалуйста, пройдите регистрацию.')
