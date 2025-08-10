from django.contrib.auth.models import User
from account.models import Profile
from telegram_bot.notifications import send_new_profile_notification
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

def create_profile(backend, user, *args, **kwargs):
    """
    Create user profile for social authentication
    """
    try:
        profile, created = Profile.objects.get_or_create(user=user)
        if created:
            send_new_profile_notification(user.username)  # Отправляем уведомление с именем пользователя
    except Exception as e:
        logger.error(f"Ошибка при создании профиля для пользователя {user.username}: {e}")

class EmailAuthBackend:
    """
    Authenticate using an e-mail address.
    """
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except (User.DoesNotExist, User.MultipleObjectsReturned) as e:
            logger.error(f"Ошибка аутентификации: {e}")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
