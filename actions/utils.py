import datetime
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Action



def create_action(user, verb, target=None, movie_url=None):
    from telegram_bot.notifications import send_movie_action_notification, send_list_action_notification
    # Проверяем, не было ли каких-либо аналогичных действий, совершенных за последнюю минуту
    now = timezone.now()
    last_minute = now - datetime.timedelta(seconds=60)
    similar_actions = Action.objects.filter(user_id=user.id, verb=verb, created__gte=last_minute)

    if target:
        target_ct = ContentType.objects.get_for_model(target)
        similar_actions = similar_actions.filter(target_ct=target_ct, target_id=target.id)

    if not similar_actions:
        # Никаких существующих действий не найдено
        action = Action(user=user, verb=verb, target=target)
        action.save()

        # Определяем, какие действия требуют уведомления
        # if verb == "добавил":
        #     send_movie_action_notification(target, movie_url, user, verb, notify_all=True)
        if verb == "опубликовал список":
            send_list_action_notification(target, movie_url, user, verb, notify_all=True)
        elif verb in [
            "добавил",
            "недавно посмотрел",
            # "понравился",
            # "не понравился",
            "прокомментировал",
            # 'добавил в "Буду смотреть"',
            # "добавил в список"
        ]:
            send_movie_action_notification(target, movie_url, user, verb)

        return True
    return False

