import os
import shutil
import django
import telebot
import logging
from django.utils import timezone
from datetime import datetime, timedelta
from decouple import config
import requests
from django.core.files.base import ContentFile


import sys
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from pytz import timezone as ZoneInfo  # fallback to pytz

logger = logging.getLogger(__name__)

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
from moviepremieres.models import Movie, Genre, Country, Director, Writer
# Инициализация бота

bot = telebot.TeleBot(config('TELEGRAM_BOT_TOKEN'))


def find_similar_movies():
    # Получаем понравившиеся фильмы пользователя
    profiles = Profile.objects.filter(telegram_connected=True)
    for profile in profiles:
        chat_id = profile.telegram_user_id
        user = profile.user
        # Получаем понравившиеся фильмы пользователя
        liked_movies = Action.objects.filter(verb='понравился', user=user).select_related('target_ct')

        # Сбор уникальных наборов жанров и создателей (режиссеры и сценаристы в одном set)
        genre_sets = set()
        creators = set()  # Объединяем режиссеров и сценаристов в один set

        for action in liked_movies:
            movie = action.target
            # Создаем frozenset для уникального набора жанров
            genre_set = frozenset(movie.genres.values_list('name', flat=True))
            genre_sets.add(genre_set)
            creators.update(movie.directors.values_list('name', flat=True))
            creators.update(movie.writers.values_list('name', flat=True))

        # Получаем кинопремьеры
        premieres = Movie.objects.all().prefetch_related('genres', 'directors', 'writers')

        # Поиск похожих фильмов
        similar_movies = []
        for movie in premieres:
            # Создаем frozenset для жанров текущего фильма
            current_genre_set = frozenset(movie.genres.values_list('name', flat=True))
            current_genres_count = len(current_genre_set)

            match_count = 0

            # Проверяем совпадения по режиссерам и сценаристам
            directors = set(movie.directors.values_list('name', flat=True))
            writers = set(movie.writers.values_list('name', flat=True))

            if directors.intersection(creators) or writers.intersection(creators):
                print(f"Совпадения по режиссерам и сценаристам - {movie.title}")
                match_count += 1

            # Проверяем совпадения по жанрам

            for genre_set in genre_sets:
                # Проверяем, что все жанры текущего фильма есть в жанрах понравившихся фильмов
                if current_genres_count > 0 and current_genre_set.issubset(genre_set):
                    if current_genres_count <= 3:
                        # Полное совпадение
                        if current_genres_count == len(genre_set):
                            print(f"Полное совпадение по жанрам - {movie.title}")
                            match_count += 1
                    elif current_genres_count > 3:
                        # Проверка на 75% совпадение
                        if current_genres_count / len(genre_set) >= 0.75:
                            print(f"На 75% совпадение по жанрам - {movie.title}")
                            match_count += 1

            # Если есть совпадения, добавляем в список
            if match_count > 0:
                similar_movies.append(movie)
        # Отправка похожих фильмов в Telegram
        if similar_movies:
            message = "На основе ваших лайков, подборка фильмов среди кинопремьер:\n"
            message += "\n".join(
                    [f"- <a href='{movie.kinopoisk_url}'>{movie.title}</a>" for movie in
                     similar_movies]) + "\n"
            bot.send_message(chat_id, message, parse_mode='HTML')

    return



def get_premieres():
    # Путь к каталогу, где хранятся постеры
    poster_directory = os.path.join(current_dir, '..', 'media', 'premieres')
    # Очистка каталога постеров
    if os.path.exists(poster_directory):
        shutil.rmtree(poster_directory)  # Удаляем весь каталог
        os.makedirs(poster_directory)  # Создаем каталог заново
    # Очистка таблиц
    Movie.objects.all().delete()
    Genre.objects.all().delete()
    Country.objects.all().delete()
    Director.objects.all().delete()
    Writer.objects.all().delete()

    # Получаем текущую дату

    now = datetime.now()
    year = now.year
    previous_year = year - 1
    month = now.strftime("%B").upper()

    params = {
        "year": year,
        "month": month
    }

    kinopoisk_premieres_url = "https://kinopoiskapiunofficial.tech/api/v2.2/films/premieres"

    try:
        premieres_movie_response = requests.get(kinopoisk_premieres_url, headers={
            'X-API-KEY': config('X-API-KEY'),
            "Content-Type": "application/json",
        }, params=params)

        premieres_movie_data = premieres_movie_response.json()
        filtered_premieres_movie_data = [
            item for item in premieres_movie_data['items']
            if item['year'] in (year, previous_year)
        ]

        for movie_data in filtered_premieres_movie_data:
                save_movie(movie_data)

    except Exception as e:
        logger.error(f"Error while getting premieres movies - {e}")


def save_movie(movie_data):
    # Сохранение информации о фильме
    try:
        movie, created = Movie.objects.get_or_create(
            kinopoisk_id=movie_data['kinopoiskId'],
            defaults={
                'title': movie_data['nameRu'],
                'title_original': movie_data['nameEn'],
                'year': movie_data['year'],
                'duration': movie_data['duration'],
                'kinopoisk_url': f"https://www.kinopoisk.ru/film/{movie_data['kinopoiskId']}",
                'premiere_date': movie_data['premiereRu'],
                # Изменено с 'posterUrl' на 'poster'
            }
        )

        # Сохранение жанров
        for genre_data in movie_data['genres']:
            genre, _ = Genre.objects.get_or_create(name=genre_data['genre'])
            movie.genres.add(genre)

        # Сохранение стран
        for country_data in movie_data['countries']:
            country, _ = Country.objects.get_or_create(name=country_data['country'])
            movie.countries.add(country)

        # Получение данных о съемочной группе
        movie_staff_url = f"https://kinopoiskapiunofficial.tech/api/v1/staff"
        try:
            movie_staff_response = requests.get(movie_staff_url, headers={
                'X-API-KEY': config('X-API-KEY2'),
                "Content-Type": "application/json",
            }, params={"filmId": movie_data['kinopoiskId']})
            movie_staff_data = movie_staff_response.json()
            if 'message' in movie_staff_data and 'You exceeded the quota' in movie_staff_data['message']:
                raise Exception("Quota exceeded for Kinopoisk API. Please try again later.")
        except Exception as e:
            logger.error(f"Error while getting movie staff - {e}")
            return

        # Сохранение режиссеров и сценаристов
        for item in movie_staff_data:
            if isinstance(item, dict):
                if item.get("professionKey", "").upper() == "DIRECTOR":
                    director_name = item["nameRu"]
                    if director_name:  # Проверка на пустое имя
                        director, _ = Director.objects.get_or_create(
                            name=director_name,
                            staff_id=item["staffId"]
                        )
                        movie.directors.add(director)
                elif item.get("professionKey", "").upper() == "WRITER":
                    writer_name = item["nameRu"]
                    if writer_name:  # Проверка на пустое имя
                        writer, _ = Writer.objects.get_or_create(
                            name=writer_name,
                            staff_id=item["staffId"]
                        )
                        movie.writers.add(writer)

        # Сохранение постера
        if movie_data.get('posterUrl'):
            poster_image = requests.get(movie_data['posterUrl'])
            extension = movie_data['posterUrl'].rsplit('.', 1)[1].lower()
            image_name = f"{movie.kinopoisk_id}.{extension}"
            movie.poster.save(image_name, ContentFile(poster_image.content), save=False)

        movie.save()  # Сохраняем объект в БД
        logger.info(f"Сохранен фильм - {movie_data['nameRu']}")

    except Exception as e:
        logger.error(f"Error while saving movie {movie_data['nameRu']} - {e}")


def send_friday_movies():
    moscow_tz = ZoneInfo('Europe/Moscow')
    # Получаем текущую дату и время
    now = timezone.now().astimezone(moscow_tz)
    # Вычисляем дату 7 дней назад
    seven_days_ago = now - timedelta(days=7)
    profiles = Profile.objects.filter(telegram_connected=True)
    site_url = config('SITE_URL')

    for profile in profiles:
        chat_id = profile.telegram_user_id

        # Получаем фильмы, добавленные в "Буду смотреть" за последние 7 дней и не просмотренные
        added_movies_to_watchlist = Action.objects.filter(
            verb='добавил в "Буду смотреть"',
            user=profile.user,
            created__gte=seven_days_ago
        )

        watched_movies_ids = Action.objects.filter(
            verb='недавно посмотрел',
            user=profile.user
        ).values_list('target_id', flat=True)

        to_watch_movies = added_movies_to_watchlist.exclude(target_id__in=watched_movies_ids)

        # Формируем сообщение
        message = "📋Фильмы, добавленные в 'Буду смотреть' за последние 7 дней и непросмотренные:\n\n"

        if to_watch_movies.exists():
            message += "\n".join([f"- <a href='{site_url}{action.target.get_absolute_url()}'>{action.target.title}</a>" for action in to_watch_movies]) + "\n"
            message += "\n😎 желаем найти время и посмотреть фильмы🍿!"
        # Отправка сообщения в Telegram
            bot.send_message(chat_id, message, parse_mode='HTML')

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
    now = timezone.now()
    # get_premieres()
    find_similar_movies()
    # if now.day == 1:
    #     send_monthly_summary()
    #     get_premieres()
    #     if now.weekday() == 4:  # 4 соответствует пятнице
    #         send_friday_movies()
    # else:
    #     if now.weekday() == 4:  # 4 соответствует пятнице
    #         send_friday_movies()
