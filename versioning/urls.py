# versioning/urls.py
from django.urls import path
from .views import changelog


urlpatterns = [
    path('changelog/', changelog, name='changelog'),
]