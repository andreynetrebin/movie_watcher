import datetime
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Action
from telegram_bot.views import send_movie_action_notification

def create_action(user, verb, target=None, movie_url=None):
# проверить, не было ли каких-либо аналогичных
# действий, совершенных за последнюю минуту
    now = timezone.now()
    last_minute = now - datetime.timedelta(seconds=60)
    similar_actions = Action.objects.filter(user_id=user.id,
        verb= verb,
        created__gte=last_minute)
    if target:
        target_ct = ContentType.objects.get_for_model(target)
        similar_actions = similar_actions.filter(
            target_ct=target_ct,
            target_id=target.id)
    if not similar_actions:
# никаких существующих действий не найдено
        action = Action(user=user, verb=verb, target=target)
        action.save()
        if verb == "недавно посмотрел":
            send_movie_action_notification(target, movie_url, user, '🍿 недавно посмотрел')
        elif verb == 'добавил в "Буду смотреть"':
            send_movie_action_notification(target, movie_url, user, '📋 добавил в "Буду смотреть"')
        elif verb == "понравился":
            send_movie_action_notification(target, movie_url, user, '👍 понравился')
        elif verb == "не понравился":
            send_movie_action_notification(target, movie_url, user, '👎 не понравился')
        elif verb == "добавил":
            send_movie_action_notification(target, movie_url, user, '🎬 добавил')
        elif verb == 'прокомментировал':
            send_movie_action_notification(target, movie_url, user, '✏️ прокомментировал')

        return True
    return False
