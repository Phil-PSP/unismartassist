"""Authentication API with mandatory MFA challenge for MFA-enabled users."""
from django.contrib.auth import authenticate
from django.core import signing
import re
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .jwt_auth import create_token_pair, refresh_access_token
from rest_framework.exceptions import AuthenticationFailed

from .mfa import issue_otp, verify_otp
from .models import User
from .serializers import UserSerializer


class TokenObtainWithMFAView(APIView):
    throttle_scope = 'auth'
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        user_id = request.data.get("user_id")
        password = request.data.get("password")
        if (
            not isinstance(user_id, str)
            or not isinstance(password, str)
            or not user_id.strip()
            or not password
            or len(user_id) > 128
            or len(password) > 1024
        ):
            return Response({"detail": "Valid user ID and password are required."}, status=400)

        user = authenticate(request, username=user_id.strip(), password=password)
        if user is None or not user.is_active:
            return Response({"detail": "Invalid credentials."}, status=401)

        if user.mfa_enabled:
            try:
                issue_otp(user, enforce_cooldown=True)
            except ValueError:
                return Response({"detail": "Please wait before requesting another verification code."}, status=429)
            except Exception:
                return Response(
                    {"detail": "Unable to send verification code. Please try again later."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            challenge = signing.dumps(
                {"user_pk": user.pk, "purpose": "api_mfa"},
                salt="accounts.api_mfa",
            )
            return Response(
                {"mfa_required": True, "challenge": challenge, "expires_in": 600},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(create_token_pair(user))


class TokenVerifyMFAView(APIView):
    throttle_scope = 'mfa'
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        challenge = request.data.get("challenge", "")
        otp = request.data.get("otp", "")
        if (
            not isinstance(challenge, str)
            or len(challenge) > 2048
            or not isinstance(otp, str)
            or not re.fullmatch(r"\d{6}", otp)
        ):
            return Response({"detail": "A valid challenge and six-digit OTP are required."}, status=400)
        try:
            payload = signing.loads(
                challenge,
                salt="accounts.api_mfa",
                max_age=600,
            )
            if payload.get("purpose") != "api_mfa":
                raise signing.BadSignature("Wrong challenge purpose")
            user = User.objects.get(pk=payload["user_pk"], is_active=True, mfa_enabled=True)
        except (signing.BadSignature, signing.SignatureExpired, KeyError, TypeError, ValueError, User.DoesNotExist):
            return Response({"detail": "Invalid or expired MFA challenge."}, status=401)

        valid, error = verify_otp(user, otp)
        if not valid:
            return Response({"detail": error}, status=401)

        return Response(create_token_pair(user))


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class LeaderboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.filter(is_active=True).order_by('-points')[:20]
        data = [
            {'name': user.get_full_name(), 'points': user.points, 'streak': user.study_streak}
            for user in users
        ]
        return Response(data)



class TokenRefreshAPIView(APIView):
    throttle_scope = 'auth'
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            access = refresh_access_token(request.data.get("refresh"))
        except AuthenticationFailed as exc:
            return Response({"detail": str(exc.detail)}, status=401)
        return Response({"access": access})
