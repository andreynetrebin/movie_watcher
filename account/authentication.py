from django.contrib.auth.models import User
from account.models import Profile
from telegram_bot.notifications import send_new_profile_notification
import logging

logger = logging.getLogger(__name__)


def create_profile(backend, user, *args, **kwargs):
    """
    Ensure every user authenticated through a social backend has a profile.

    This step is intentionally idempotent: it also repairs older social-auth
    accounts that were created before profile creation was added to the pipeline.
    """
    if user is None:
        return

    profile, created = Profile.objects.get_or_create(user=user)
    if created:
        try:
            send_new_profile_notification(user.username)
        except Exception:
            # A Telegram outage must not prevent a user from signing in.
            logger.exception(
                "Не удалось отправить уведомление о регистрации пользователя %s",
                user.username,
            )


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
