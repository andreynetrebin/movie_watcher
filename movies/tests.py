from .forms import MovieCreateForm
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Movie, Genre, Director, Writer
from django import forms
from unittest.mock import patch

class MovieModelTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.genre = Genre.objects.create(name='Drama')
        self.director = Director.objects.create(name='Director Name', staff_id=1)
        self.writer = Writer.objects.create(name='Writer Name', staff_id=1)
        self.movie = Movie.objects.create(
            title='Test Movie',
            year=2023,
            kinopoisk_id=123456,
            kinopoisk_url='https://www.kinopoisk.ru/film/123456/',
            description='Test description',
            poster='path/to/poster.jpg',
            movie_json={},
            movie_staff_json={}
        )
        self.movie.genres.add(self.genre)
        self.movie.directors.add(self.director)
        self.movie.writers.add(self.writer)

    def test_add_like(self):
        self.movie.add_like(self.user)
        self.assertIn(self.user, self.movie.users_like.all())
        self.assertEqual(self.movie.total_likes, 1)

    def test_remove_like(self):
        self.movie.add_like(self.user)
        self.movie.remove_like(self.user)
        self.assertNotIn(self.user, self.movie.users_like.all())
        self.assertEqual(self.movie.total_likes, 0)

    def test_add_dislike(self):
        self.movie.add_dislike(self.user)
        self.assertIn(self.user, self.movie.users_dislike.all())
        self.assertEqual(self.movie.total_dislikes, 1)

    def test_remove_dislike(self):
        self.movie.add_dislike(self.user)
        self.movie.remove_dislike(self.user)
        self.assertNotIn(self.user, self.movie.users_dislike.all())
        self.assertEqual(self.movie.total_dislikes, 0)

    def test_add_like_removes_dislike(self):
        self.movie.add_dislike(self.user)
        self.movie.add_like(self.user)
        self.assertNotIn(self.user, self.movie.users_dislike.all())
        self.assertEqual(self.movie.total_dislikes, 0)
        self.assertEqual(self.movie.total_likes, 1)

    def test_add_dislike_removes_like(self):
        self.movie.add_like(self.user)
        self.movie.add_dislike(self.user)
        self.assertNotIn(self.user, self.movie.users_like.all())
        self.assertEqual(self.movie.total_likes, 0)
        self.assertEqual(self.movie.total_dislikes, 1)

class MovieCreateFormTests(TestCase):

    @patch('requests.get')
    def test_valid_form(self, mock_get):
        mock_get.return_value.json.return_value = {
            "nameRu": "Тестовый фильм ",
            "nameOriginal": "Test Movie",
            "year": 2023,
            "filmLength": 120,
            "webUrl": "https://www.kinopoisk.ru/film/123456/",
            "description": "Описание тестового фильма",
            "posterUrl": "https://example.com/poster.jpg",
            "countries": [{"country": "Россия"}],
            "genres": [{"genre": "Драма"}],
            "type": "FILM",
            "serial": False
        }

        form_data = {
            'url': 'https://www.kinopoisk.ru/film/123456/',
        }
        form = MovieCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_url_format(self):
        form_data = {
            'url': 'invalid_url',
        }
        form = MovieCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)

    @patch('requests.get')
    def test_existing_movie(self, mock_get):
        Movie.objects.create(
            kinopoisk_id=123456,
            title='Существующий фильм',
            year=2023,
            kinopoisk_url='https://www.kinopoisk.ru/film/123456/',
            description='Описание существующего фильма',
            poster='path/to/poster.jpg',
            movie_json={},
            movie_staff_json={}
        )

        mock_get.return_value.json.return_value = {
            "nameRu": "Существующий фильм",
            "nameOriginal": "Existing Movie",
            "year": 2023,
            "filmLength": 120,
            "webUrl": "https://www.kinopoisk.ru/film/123456/",
            "description": "Описание существующего фильма",
            "posterUrl": "https://example.com/poster.jpg",
            "countries": [{"country": "Россия"}],
            "genres": [{"genre": "Драма"}],
            "type": "FILM",
            "serial": False
        }

        form_data = {
            'url': 'https://www.kinopoisk.ru/film/123456/',
        }
        form = MovieCreateForm(data=form_data, source='website')
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)

    @patch('requests.get')
    def test_save_method(self, mock_get):
        mock_get.return_value.json.return_value = {
            "nameRu": "Тестовый фильм",
            "nameOriginal": "Test Movie",
            "year": 2023,
            "filmLength": 120,
            "webUrl": "https://www.kinopoisk.ru/film/123456/",
            "description": "Описание тестового фильма",
            "posterUrl": "https://example.com/poster.jpg",
            "countries": [{"country": "Россия"}],
            "genres": [{"genre": "Драма"}],
            "type": "FILM",
            "serial": False
        }

        mock_get.return_value.content = b'fake_image_content'  # Возвращаем байтовый объект
        form_data = {
            'url': 'https://www.kinopoisk.ru/film/123456/',
        }
        form = MovieCreateForm(data=form_data)
        if form.is_valid():
            movie = form.save(commit=False)
            self.assertIsInstance(movie, Movie)
            self.assertEqual(movie.title, "Тестовый фильм")
            self.assertEqual(movie.year, 2023)