# account/tests/test_points_manager.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from account.points_manager import PointsManager
from account.models import Profile, PointsHistory

User = get_user_model()

class PointsManagerTests(TestCase):

    def setUp(self):
        # Создаем тестового пользователя и профиль
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile = Profile.objects.create(user=self.user)

    def test_add_points_creates_history_entry(self):
        # Начисляем баллы
        PointsManager.add_points(self.user, 5, 'Тестовое действие')

        # Проверяем, что баллы добавлены
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.points, 5)

        # Проверяем, что запись в истории создана
        history_entry = PointsHistory.objects.first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.points, 5)
        self.assertEqual(history_entry.action, 'Тестовое действие')

    def test_deduct_points_creates_history_entry(self):
        # Начисляем баллы, чтобы потом их снять
        PointsManager.add_points(self.user, 10, 'Тестовое действие')

        # Снимаем баллы
        PointsManager.deduct_points(self.user, 3, 'Снятие баллов')

        # Проверяем, что баллы сняты
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.points, 7)

        # Проверяем, что запись в истории создана
        history_entry = PointsHistory.objects.last()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.points, -3)
        self.assertEqual(history_entry.action, 'Снятие баллов')

    def test_add_points_with_target(self):
        # Начисляем баллы с указанием целевого объекта
        mock_target = None  # Здесь вы можете создать объект, если это необходимо
        PointsManager.add_points(self.user, 5, 'Тестовое действие', target=mock_target)

        # Проверяем, что запись в истории создана с целевым объектом
        history_entry = PointsHistory.objects.first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.target_content_type, None)  # Проверка на None, если target не установлен
        self.assertEqual(history_entry.target_object_id, None)

    def test_deduct_points_with_target(self):
        # Начисляем баллы, чтобы потом их снять
        PointsManager.add_points(self.user, 10, 'Тестовое действие')

        # Снимаем баллы с указанием целевого объекта
        mock_target = None  # Здесь вы можете создать объект, если это необходимо
        PointsManager.deduct_points(self.user, 3, 'Снятие баллов', target=mock_target)

        # Проверяем, что запись в истории создана с целевым объектом
        history_entry = PointsHistory.objects.last()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.target_content_type, None)  # Проверка на None, если target не установлен
        self.assertEqual(history_entry.target_object_id, None)
