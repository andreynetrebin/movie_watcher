"""
Test settings for environments where the configured MySQL account cannot
create databases (for example, PythonAnywhere shared MySQL).

Run tests with:
    python manage.py test account --settings=movie_watcher.test_settings

The test runner creates an isolated in-memory SQLite database. Production
settings and the configured MySQL database are not modified.
"""
from .settings import *  # noqa: F403,F401


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Avoid expensive password hashing in automated tests.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
