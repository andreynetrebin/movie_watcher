from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from account.authentication import create_profile
from account.models import Profile


User = get_user_model()


class SocialAuthProfilePipelineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="social-user",
            email="social-user@example.com",
            password="test-password",
        )

    @patch("account.authentication.send_new_profile_notification")
    def test_creates_profile_for_new_social_auth_user(self, notify):
        create_profile(backend=None, user=self.user)

        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        notify.assert_called_once_with(self.user.username)

    @patch("account.authentication.send_new_profile_notification")
    def test_does_not_duplicate_existing_profile(self, notify):
        existing_profile = Profile.objects.create(user=self.user)

        create_profile(backend=None, user=self.user)

        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        self.assertEqual(existing_profile.pk, self.user.profile.pk)
        notify.assert_not_called()

    @patch(
        "account.authentication.send_new_profile_notification",
        side_effect=RuntimeError("Telegram is unavailable"),
    )
    def test_notification_failure_does_not_break_profile_creation(self, notify):
        create_profile(backend=None, user=self.user)

        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        notify.assert_called_once_with(self.user.username)

    def test_skips_missing_pipeline_user(self):
        create_profile(backend=None, user=None)

        self.assertEqual(Profile.objects.count(), 0)
