# lists/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from movies.models import MovieList

User = get_user_model()

class MovieListTests(TestCase):

    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        # Создаем тестовый список фильмов
        self.movie_list = MovieList.objects.create(title='My Movie List', user=self.user)

    def test_create_movie_list(self):
        response = self.client.post(reverse('lists:create_movie_list'), {'title': 'New Movie List'})
        self.assertEqual(response.status_code, 302)  # Проверяем, что происходит редирект
        self.assertTrue(MovieList.objects.filter(title='New Movie List').exists())  # Проверяем, что список создан

    def test_movie_list_detail(self):
        response = self.client.get(reverse('lists:movie_list_detail', args=[self.movie_list.id]))
        self.assertEqual(response.status_code, 200)  # Проверяем, что страница загружается
        self.assertContains(response, 'My Movie List')  # Проверяем, что заголовок списка присутствует

    def test_like_movie_list(self):
        response = self.client.post(reverse('lists:like_movie_list', args=[self.movie_list.id]))
        self.assertEqual(response.status_code, 302)  # Проверяем, что происходит редирект
        self.assertIn(self.user, self.movie_list.users_like.all())  # Проверяем, что пользователь добавлен в лайки

        # Проверяем, что повторное нажатие убирает лайк
        response = self.client.post(reverse('lists:like_movie_list', args=[self.movie_list.id]))
        self.assertNotIn(self.user, self.movie_list.users_like.all())  # Проверяем, что пользователь убран из лайков

    def test_add_movies_to_list(self):
        # Здесь мы не добавляем фильм, так как он не нужен для тестов
        response = self.client.post(reverse('lists:add_movies_to_list', args=[self.movie_list.id]), {'movies': []})
        self.assertEqual(response.status_code, 200)  # Проверяем, что страница загружается
        # Проверяем, что список фильмов остается пустым
        self.assertEqual(self.movie_list.movies.count(), 0)

    def test_view_movie_list(self):
        response = self.client.get(reverse('lists:view_movie_list', args=[self.movie_list.id]))
        self.assertEqual(response.status_code, 200)  # Проверяем, что страница загружается
        self.assertContains(response, 'My Movie List')  # Проверяем, что заголовок списка присутствует

    def test_users_movie_lists(self):
        response = self.client.get(reverse('lists:users_movie_lists'))
        self.assertEqual(response.status_code, 200)  # Проверяем, что страница загружается
        self.assertContains(response, 'My Movie List')  # Проверяем, что заголовок списка присутствует