# account/points_manager.py
from .models import PointsHistory, Profile
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

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
        points_history = PointsHistory(
            user=user,
            points=points,
            action=action,
        )
        if target:
            points_history.target_content_type = ContentType.objects.get_for_model(target)
            points_history.target_object_id = target.id
        points_history.save()

    @staticmethod
    def deduct_points(user: User, points: int, action: str, target=None):
        """Снимает баллы у пользователя и сохраняет запись в истории."""
        profile, created = Profile.objects.get_or_create(user=user)  # Убедитесь, что профиль существует
        profile.points -= points
        profile.save()

        # Сохраняем запись о снятии баллов

        points_history = PointsHistory(
            user=user,
            points=-points,
            action=action,
        )
        if target:
            points_history.target_content_type = ContentType.objects.get_for_model(target)
            points_history.target_object_id = target.id
        points_history.save()