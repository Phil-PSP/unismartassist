from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from .mfa import hash_otp, verify_otp, issue_otp
from .forms import SignupForm
from .models import User


class MFAHelperTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id="MFA/TEST/01",
            email="mfa-test@example.com",
            password="A-Strong-Test-Password-2026!",
            first_name="Test",
            last_name="User",
            mfa_enabled=True,
        )

    def test_otp_is_stored_as_hash_and_valid_code_is_single_use(self):
        self.user.mfa_secret = hash_otp(self.user, "123456")
        from django.utils import timezone
        from datetime import timedelta
        self.user.mfa_secret_expires = timezone.now() + timedelta(minutes=10)
        self.user.save()
        self.assertNotEqual(self.user.mfa_secret, "123456")
        ok, error = verify_otp(self.user, "123456")
        self.assertTrue(ok)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertEqual(self.user.mfa_secret, "")

    def test_five_incorrect_attempts_invalidate_code(self):
        from django.utils import timezone
        from datetime import timedelta
        self.user.mfa_secret = hash_otp(self.user, "123456")
        self.user.mfa_secret_expires = timezone.now() + timedelta(minutes=10)
        self.user.save()
        for _ in range(5):
            verify_otp(self.user, "000000")
        self.user.refresh_from_db()
        self.assertEqual(self.user.mfa_attempts, 5)
        self.assertEqual(self.user.mfa_secret, "")


class MFATokenAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id="MFA/API/01",
            email="api-test@example.com",
            password="A-Strong-Test-Password-2026!",
            first_name="API",
            last_name="Test",
            mfa_enabled=True,
        )

    @patch("apps.accounts.mfa.send_mail")
    def test_password_step_does_not_issue_jwt_when_mfa_is_enabled(self, mocked_mail):
        response = self.client.post(
            "/api/accounts/token/",
            {"user_id": self.user.user_id, "password": "A-Strong-Test-Password-2026!"},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data["mfa_required"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        mocked_mail.assert_called_once()

    @patch("apps.accounts.mfa.send_mail")
    def test_correct_otp_issues_jwt_after_password_challenge(self, mocked_mail):
        from apps.accounts.mfa import hash_otp
        from django.utils import timezone
        from datetime import timedelta
        from django.core import signing

        self.user.mfa_secret = hash_otp(self.user, "654321")
        self.user.mfa_secret_expires = timezone.now() + timedelta(minutes=10)
        self.user.save()
        challenge = signing.dumps(
            {"user_pk": self.user.pk, "purpose": "api_mfa"},
            salt="accounts.api_mfa",
        )
        response = self.client.post(
            "/api/accounts/token/verify/",
            {"challenge": challenge, "otp": "654321"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


    def test_wrong_otp_never_returns_tokens(self):
        from apps.accounts.mfa import hash_otp
        from django.utils import timezone
        from datetime import timedelta
        from django.core import signing
        self.user.mfa_secret = hash_otp(self.user, "654321")
        self.user.mfa_secret_expires = timezone.now() + timedelta(minutes=10)
        self.user.save()
        challenge = signing.dumps(
            {"user_pk": self.user.pk, "purpose": "api_mfa"},
            salt="accounts.api_mfa",
        )
        response = self.client.post(
            "/api/accounts/token/verify/",
            {"challenge": challenge, "otp": "111111"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)



class PasswordPolicyTests(APITestCase):
    def test_signup_rejects_weak_password(self):
        form = SignupForm(data={
            "first_name": "New",
            "last_name": "Student",
            "user_id": "NEW/STUDENT/01",
            "email": "new-student@example.com",
            "password": "123456",
            "confirm_password": "123456",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)


class OTPResendPolicyTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id="MFA/COOLDOWN/01",
            email="mfa-cooldown@example.com",
            password="A-Strong-Test-Password-2026!",
            first_name="Cooldown",
            last_name="Test",
            mfa_enabled=True,
        )

    @patch("apps.accounts.mfa.send_mail")
    def test_otp_resend_is_blocked_during_cooldown(self, mocked_mail):
        issue_otp(self.user)
        with self.assertRaises(ValueError):
            issue_otp(self.user, enforce_cooldown=True)
        mocked_mail.assert_called_once()



class JWTTokenAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id="JWT/API/01",
            email="jwt-api@example.com",
            password="A-Strong-Test-Password-2026!",
            first_name="JWT",
            last_name="Tester",
            mfa_enabled=False,
        )

    def test_password_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            "/api/accounts/token/",
            {"user_id": self.user.user_id, "password": "A-Strong-Test-Password-2026!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_endpoint_accepts_refresh_token_only(self):
        from .jwt_auth import create_token_pair
        pair = create_token_pair(self.user)
        response = self.client.post(
            "/api/accounts/token/refresh/",
            {"refresh": pair["refresh"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

        rejected = self.client.post(
            "/api/accounts/token/refresh/",
            {"refresh": pair["access"]},
            format="json",
        )
        self.assertEqual(rejected.status_code, 401)

    def test_access_token_authenticates_and_refresh_token_is_rejected(self):
        from .jwt_auth import create_token_pair
        pair = create_token_pair(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + pair["access"])
        response = self.client.get("/api/accounts/profile/")
        self.assertEqual(response.status_code, 200)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + pair["refresh"])
        response = self.client.get("/api/accounts/profile/")
        self.assertEqual(response.status_code, 401)
