import os
from django.contrib.auth.backends import BaseBackend


class EnvAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        expected_user = os.environ.get("AUTH_USERNAME")
        expected_pass = os.environ.get("AUTH_PASSWORD")

        if not expected_user or not expected_pass:
            return None

        if username == expected_user and password == expected_pass:
            return SimpleUser(username=username)
        return None

    def get_user(self, user_id):
        if user_id == 1:
            expected_user = os.environ.get("AUTH_USERNAME", "admin")
            return SimpleUser(username=expected_user)
        return None


class SimpleUser:
    def __init__(self, username):
        self.id = 1
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        self.pk = 1

    def __str__(self):
        return self.username
