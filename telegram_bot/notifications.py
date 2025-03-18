import logging
import telebot
from django.contrib.auth import get_user_model
from django.urls import reverse
from account.models import Profile
from decouple import config

User  = get_user_model()
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(config('TELEGRAM_BOT_TOKEN'))

def send_version_notification(version_number, release_date, changes):
    emoji = "📢"  # Эмодзи для сообщения
    message = (
        f"{emoji} *Выпущена версия:* {version_number}\n"
        f"*Дата:* {release_date}\n"
        f"*Изменения:*\n{changes}\n\n"
        f"🔗 [Полный перечень изменений]({config('SITE_URL')}/versioning/changelog/)"
    )
    profiles = Profile.objects.filter(telegram_connected=True)
    for profile in profiles:
        chat_id = profile.telegram_user_id
        bot.send_message(chat_id, message, parse_mode='Markdown')

def send_movie_action_notification(movie, movie_url, action_user, action, notify_all=False):
    if action in ["добавил", "понравился", "не понравился", "прокомментировал", "добавил в список", "недавно посмотрел", 'добавил в "Буду смотреть"']:
        if notify_all:
            subscribers = User.objects.exclude(id=action_user.id).filter(profile__telegram_connected=True)
        else:
            subscribers = action_user.followers.filter(profile__telegram_connected=True)

        logger.info(f"Found {subscribers.count()} subscribers for {action_user.username}")

        actions = {
            'недавно посмотрел': 'Недавно_посмотрел🍿',
            'добавил': 'Добавил🎬',
            'добавил в "Буду смотреть"': 'Будет_смотреть📋',
            'добавил в список': 'Добавил_в_список🎞',
            'понравился': 'Понравился👍',
            'не понравился': 'Не_понравился👎',
            'прокомментировал': 'Прокомментировал✏️',
        }

        hashtag = actions.get(action)

        for subscriber in subscribers:
            subscriber_profile = Profile.objects.get(user=subscriber)
            chat_id = subscriber_profile.telegram_user_id

            if chat_id:
                message = (
                    f"<b>{action_user.first_name} {action_user.last_name}</b> {action} <b>{movie.title}</b>.\n"
                    f"Ссылка на Кинопоиск: {movie.kinopoisk_url}\n"
                    f"Ссылка на страницу фильма: {movie_url}\n\n\n"
                    f"#{action_user.first_name}_{action_user.last_name}😊\n"
                    f"#{hashtag}" if hashtag else ""
                )
                try:
                    bot.send_message(chat_id, message, parse_mode='HTML')
                    logger.info(f"Message sent to {subscriber.username} ({chat_id})")
                except Exception as e:
                    logger.error(f"Error sending message to {chat_id}: {e}")
            else:
                logger.warning(f"No Telegram ID for subscriber: {subscriber.username}")

def send_new_profile_notification(username):
    profiles = Profile.objects.filter(telegram_connected=True)
    for profile in profiles:
        chat_id = profile.telegram_user_id
        profile_url = reverse('user_detail', kwargs={'username': username})
        site_url = config('SITE_URL')
        message = (
            f"Зарегистрировался новый пользователь - <b>{username}</b>\n"
            f"Ссылка на профиль🤙: {site_url}{profile_url}\n\n"
            f"#новый_пользователь"
        )
        bot.send_message(chat_id, message, parse_mode='HTML')
