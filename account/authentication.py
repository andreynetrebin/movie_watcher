from django.contrib.auth.models import User
from account.models import Profile
from telegram_bot.views import send_new_profile_notification

def create_profile(backend, user, *args, **kwargs):
    """
    Create user profile for social authentication
    """
    profile, created = Profile.objects.get_or_create(user=user)
    if created:
        send_new_profile_notification(user.username)  # Отправляем уведомление с именем пользователя

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
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None