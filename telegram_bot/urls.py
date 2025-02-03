# telegram_bot/urls.py
from django.urls import path
from . import views

app_name = 'telegram_bot'

urlpatterns = [
    path('', views.telegram_webhook, name='telegram_webhook'),
]