# account/points_manager.py
from .models import PointsHistory, Profile
from django.contrib.auth.models import User

class PointsManager:
    POINTS_FOR_WATCHING = 1
    POINTS_FOR_COMMENT = 2
    POINTS_FOR_ADDING_MOVIE = 3
    POINTS_FOR_CREATING_LIST = 5
    POINTS_FOR_LIKING_LIST = 3

    @staticmethod
    def add_points(user: User, points: int, action: str, target=None):
        """Начисляет баллы пользователю и сохраняет запись в истории."""
        profile, created = Profile.objects.get_or_create(user=user)  # Убедитесь, что профиль существует
        profile.points += points
        profile.save()

        # Сохраняем запись о начислении баллов
        PointsHistory.objects.create(user=user, points=points, action=action, target=target)

    @staticmethod
    def deduct_points(user: User, points: int, action: str, target=None):
        """Снимает баллы у пользователя и сохраняет запись в истории."""
        profile, created = Profile.objects.get_or_create(user=user)  # Убедитесь, что профиль существует
        profile.points -= points
        profile.save()

        # Сохраняем запись о снятии баллов
        PointsHistory.objects.create(user=user, points=-points, action=action, target=target)