from datetime import timedelta

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from auth.backends import EnvAuthBackend
from auth.serializers import LoginSerializer, UserSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        backend = EnvAuthBackend()
        user = backend.authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = AccessToken()
        token.set_exp(lifetime=timedelta(hours=24))
        token["user_id"] = user.pk
        token["username"] = user.username

        response = Response(
            {"access_token": str(token), "token_type": "bearer", "username": user.username}
        )

        response.set_cookie(
            key="access_token",
            value=str(token),
            httponly=True,
            samesite="lax",
            max_age=24 * 60 * 60,
            secure=not settings.DEBUG,
        )

        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({"message": "Logged out"})
        response.delete_cookie(key="access_token", httponly=True, samesite="lax")
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
