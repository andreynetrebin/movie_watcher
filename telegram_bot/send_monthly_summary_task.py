import os
import django
import telebot
from django.utils import timezone
from datetime import datetime, timedelta
from decouple import config
import sys
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from pytz import timezone as ZoneInfo  # fallback to pytz

# Получаем путь к текущему файлу
current_dir = os.path.dirname(os.path.abspath(__file__))

# Определяем путь к проекту, который находится на один уровень ниже
parent_dir = os.path.dirname(current_dir)

# Добавляем путь к проекту в sys.path
sys.path.append(parent_dir)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_watcher.settings')
django.setup()

# Импорт моделей после настройки Django
from account.models import Profile
from actions.models import Action
# Инициализация бота

bot = telebot.TeleBot(config('TELEGRAM_BOT_TOKEN'))

def send_monthly_summary():
    # Часовой пояс Москвы
    moscow_tz = ZoneInfo('Europe/Moscow')
    # Получаем текущую дату и время с учетом временной зоны (UTC или активной зоны)
    now = timezone.now()
    # Вычисляем первый день текущего месяца
    first_day_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Вычисляем последний день предыдущего месяца
    last_day_previous_month = first_day_current_month - timedelta(days=1)
    # Определяем год и месяц предыдущего месяца
    year_prev = last_day_previous_month.year
    month_prev = last_day_previous_month.month
    # Формируем datetime для начала предыдущего месяца (1 число, 00:00:00) в московском времени
    start_of_previous_month_naive = datetime(year_prev, month_prev, 1, 0, 0, 0, 0)
    # Формируем datetime для конца предыдущего месяца (последний день, 23:59:59.999000) в московском времени
    end_of_previous_month_naive = datetime(year_prev, month_prev, last_day_previous_month.day, 23, 59, 59, 999000)
    # Делаем datetime aware, локализуем в московский часовой пояс
    start_of_previous_month = start_of_previous_month_naive.replace(tzinfo=moscow_tz)
    end_of_previous_month = end_of_previous_month_naive.replace(tzinfo=moscow_tz)
    # Получаем действия пользователей за предыдущий месяц
    actions = Action.objects.filter(created__gte=start_of_previous_month,
                                     created__lt=end_of_previous_month)

    profiles = Profile.objects.filter(telegram_connected=True)
    site_url = config('SITE_URL')

    for profile in profiles:
        chat_id = profile.telegram_user_id
        # Сбор информации о действиях
        watched_movies = actions.filter(verb='недавно посмотрел', user=profile.user)
        added_movies = actions.filter(verb='добавил', user=profile.user)
        added_movies_to_watchlist = actions.filter(verb='добавил в "Буду смотреть"', user=profile.user)
        published_lists = actions.filter(verb='опубликовал список', user=profile.user)

        # Фильтруем добавленные фильмы, которые не были просмотрены
        watched_movies_ids = watched_movies.values_list('target_id', flat=True)  # Изменено на target_id
        to_watch_movies = added_movies_to_watchlist.exclude(target_id__in=watched_movies_ids)  # Изменено на target_id

        # Формируем сообщение
        message = "Ваши активности за предыдущий месяц:\n\n"

        # Добавленные фильмы
        added_count = added_movies.count()
        if added_count > 0:
            message += f"🎬Добавили {added_count} фильмов.\n"
        else:
            message += "😳Очень жаль, что Вы не добавили ни одного фильма.\n"
        message += "\n"
        # Просмотренные фильмы
        watched_count = watched_movies.count()
        if watched_count > 0:
            message += f"🍿Посмотрели {watched_count} фильмов:\n"
            message += "\n".join([f"- <a href='{site_url}{action.target.get_absolute_url()}'>{action.target.title}</a>" for action in watched_movies]) + "\n"
        else:
            message += "😳Не посмотрели ни одного фильма.\n"
        message += "\n"

        # Добавленные в "Буду смотреть"
        to_watch_count = added_movies_to_watchlist.count()
        unseen_to_watch_movies = to_watch_movies.count()
        if to_watch_count > 0:
            message += f"📋Добавили в 'Буду смотреть' {to_watch_count} фильмов.\nИз них остались не просмотренными - {unseen_to_watch_movies} фильмов:\n"
            message += "\n".join([f"- <a href='{site_url}{action.target.get_absolute_url()}'>{action.target.title}</a>" for action in to_watch_movies]) + "\n"
        else:
            message += f"😳Ничего не добавили в 'Буду смотреть'.\n"
        message += "\n"

        # Опубликованные списки фильмов
        published_count = published_lists.count()
        if published_count > 0:
            message += f"🎞Опубликовали {published_count} списков фильмов:\n"
            message += "\n".join([f"- <a href='{site_url}{action.target.get_absolute_url()}'>{action.target.title}</a>" for action in published_lists]) + "\n"
        else:
            message += "Не опубликовали ни одного списка фильмов.\n"
        message += "\n"

        # Отправка сообщения в Telegram
        bot.send_message(chat_id, message, parse_mode='HTML')

if __name__ == "__main__":
    send_monthly_summary()