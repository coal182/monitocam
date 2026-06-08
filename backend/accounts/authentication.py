from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.request import Request

from accounts.backends import EnvAuthBackend


class JWTCookieAuthentication(JWTAuthentication):
    def authenticate(self, request: Request):
        token = request.COOKIES.get("access_token")

        if not token:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            return None

        try:
            validated_token = self.get_validated_token(token)
            user = self.get_user(validated_token)
            return user, validated_token
        except (InvalidToken, TokenError):
            return None

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        backend = EnvAuthBackend()
        user = backend.get_user(user_id)
        if user is not None:
            return user
        return super().get_user(validated_token)
