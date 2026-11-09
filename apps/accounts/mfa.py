"""Shared MFA helpers for web and API authentication."""
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

OTP_TTL = timedelta(minutes=10)
OTP_RESEND_COOLDOWN = timedelta(seconds=60)
OTP_MAX_ATTEMPTS = 5


def generate_otp():
    return f"{secrets.randbelow(900000) + 100000:06d}"


def hash_otp(user, otp):
    value = f"{user.pk}:{otp}"
    return salted_hmac("accounts.mfa_otp", value, secret=settings.SECRET_KEY).hexdigest()


def issue_otp(user, *, enforce_cooldown=False):
    """Create one OTP under a row lock, then deliver it without holding a DB lock."""
    with transaction.atomic():
        locked_user = user.__class__.objects.select_for_update().get(pk=user.pk)
        now = timezone.now()
        if (
            enforce_cooldown
            and locked_user.mfa_last_sent_at
            and now - locked_user.mfa_last_sent_at < OTP_RESEND_COOLDOWN
        ):
            raise ValueError("Please wait before requesting another code.")

        otp = generate_otp()
        otp_hash = hash_otp(locked_user, otp)
        locked_user.mfa_secret = otp_hash
        locked_user.mfa_secret_expires = now + OTP_TTL
        locked_user.mfa_attempts = 0
        locked_user.mfa_last_sent_at = now
        locked_user.save(update_fields=[
            "mfa_secret", "mfa_secret_expires", "mfa_attempts", "mfa_last_sent_at"
        ])
        recipient = locked_user.personal_email or locked_user.email
        first_name = locked_user.first_name

    try:
        send_mail(
            subject="KAAF University — Your Login OTP",
            message=(
                f"Hello {first_name},\\n\\n"
                f"Your one-time password (OTP) is: {otp}\\n\\n"
                "This code expires in 10 minutes. Do not share it with anyone.\\n\\n"
                "KAAF University Smart Assistant"
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@kaafuni.edu.gh"),
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        # Do not clear a newer code issued by a concurrent request.
        with transaction.atomic():
            current = user.__class__.objects.select_for_update().get(pk=user.pk)
            if current.mfa_secret == otp_hash:
                current.mfa_secret = ""
                current.mfa_secret_expires = None
                current.mfa_last_sent_at = None
                current.save(update_fields=["mfa_secret", "mfa_secret_expires", "mfa_last_sent_at"])
        raise
    return otp


def verify_otp(user, submitted_otp):
    """Verify and consume an OTP atomically so it cannot be used twice."""
    with transaction.atomic():
        locked_user = user.__class__.objects.select_for_update().get(pk=user.pk)
        now = timezone.now()
        if locked_user.mfa_attempts >= OTP_MAX_ATTEMPTS:
            return False, "Too many incorrect attempts. Request a new code."
        if not locked_user.mfa_secret or not locked_user.mfa_secret_expires:
            return False, "No active code. Request a new code."
        if now > locked_user.mfa_secret_expires:
            locked_user.mfa_secret = ""
            locked_user.mfa_secret_expires = None
            locked_user.mfa_last_sent_at = None
            locked_user.save(update_fields=["mfa_secret", "mfa_secret_expires", "mfa_last_sent_at"])
            return False, "Your code has expired. Request a new one."

        candidate = hash_otp(locked_user, str(submitted_otp or "").strip())
        if not hmac.compare_digest(locked_user.mfa_secret, candidate):
            locked_user.mfa_attempts += 1
            fields = ["mfa_attempts"]
            if locked_user.mfa_attempts >= OTP_MAX_ATTEMPTS:
                locked_user.mfa_secret = ""
                locked_user.mfa_secret_expires = None
                locked_user.mfa_last_sent_at = None
                fields += ["mfa_secret", "mfa_secret_expires", "mfa_last_sent_at"]
            locked_user.save(update_fields=fields)
            return False, "Invalid code. Please try again."

        locked_user.mfa_secret = ""
        locked_user.mfa_secret_expires = None
        locked_user.mfa_attempts = 0
        locked_user.mfa_last_sent_at = None
        locked_user.save(update_fields=[
            "mfa_secret", "mfa_secret_expires", "mfa_attempts", "mfa_last_sent_at"
        ])
        return True, None
