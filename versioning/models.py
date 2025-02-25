# versioning/models.py
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from account.models import Profile
from telegram_bot.views import send_version_notification  # Импортируем функцию

class Version(models.Model):
    version_number = models.CharField(max_length=10)
    release_date = models.DateField()
    changes = models.TextField()

    def __str__(self):
        return self.version_number

# Сигнал для отправки уведомления после сохранения новой версии
@receiver(post_save, sender=Version)
def notify_users_on_version_creation(sender, instance, created, **kwargs):
    if created:
        send_version_notification(instance.version_number, instance.release_date, instance.changes)