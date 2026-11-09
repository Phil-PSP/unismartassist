"""JWT issuance and authentication for the KAAF API.

The token claims intentionally match SimpleJWT's default claim names so existing
clients can continue sending existing access/refresh tokens during migration.
"""
import uuid
from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

ACCESS_TOKEN_LIFETIME = timedelta(hours=1)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)
ALGORITHM = "HS256"
User = get_user_model()


def create_token(user, token_type):
    if token_type not in {"access", "refresh"}:
        raise ValueError("Unsupported token type.")
    now = timezone.now()
    lifetime = ACCESS_TOKEN_LIFETIME if token_type == "access" else REFRESH_TOKEN_LIFETIME
    payload = {
        "token_type": token_type,
        "exp": now + lifetime,
        "iat": now,
        "jti": uuid.uuid4().hex,
        "user_id": user.pk,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(user):
    return {
        "refresh": create_token(user, "refresh"),
        "access": create_token(user, "access"),
    }


def decode_token(token):
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["exp", "iat", "jti", "token_type", "user_id"]},
    )


class JWTAuthentication(BaseAuthentication):
    """Authenticate Bearer access tokens; never accept refresh tokens as access."""

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != b"bearer":
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid Authorization header.")

        try:
            token = parts[1].decode("utf-8")
            payload = decode_token(token)
        except (UnicodeDecodeError, jwt.InvalidTokenError):
            raise AuthenticationFailed("Invalid or expired access token.")

        if payload.get("token_type") != "access":
            raise AuthenticationFailed("An access token is required.")

        user_id = payload.get("user_id")
        if not isinstance(user_id, (str, int)) or isinstance(user_id, bool):
            raise AuthenticationFailed("Invalid token subject.")
        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except (User.DoesNotExist, TypeError, ValueError):
            raise AuthenticationFailed("User is inactive or no longer exists.")

        return (user, token)

    def authenticate_header(self, request):
        return "Bearer"


def refresh_access_token(refresh_token):
    """Validate a refresh token and return a fresh access token for an active user."""
    if not isinstance(refresh_token, str) or not refresh_token or len(refresh_token) > 4096:
        raise AuthenticationFailed("A valid refresh token is required.")
    try:
        payload = decode_token(refresh_token)
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid or expired refresh token.")

    if payload.get("token_type") != "refresh":
        raise AuthenticationFailed("A refresh token is required.")

    user_id = payload.get("user_id")
    if not isinstance(user_id, (str, int)) or isinstance(user_id, bool):
        raise AuthenticationFailed("Invalid refresh token subject.")
    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except (User.DoesNotExist, TypeError, ValueError):
        raise AuthenticationFailed("User is inactive or no longer exists.")

    return create_token(user, "access")
