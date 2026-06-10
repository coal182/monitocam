import os
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ.setdefault("AUTH_USERNAME", "testuser")
os.environ.setdefault("AUTH_PASSWORD", "testpass")


@pytest.mark.django_db
class TestAuth:
    def test_login_success(self, client):
        response = client.post(
            "/auth/login/",
            {"username": "testuser", "password": "testpass"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "testuser"

    def test_login_invalid_credentials(self, client):
        response = client.post(
            "/auth/login/",
            {"username": "wrong", "password": "wrong"},
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_me_authenticated(self, client):
        login_response = client.post(
            "/auth/login/",
            {"username": "testuser", "password": "testpass"},
            content_type="application/json",
        )
        token = login_response.json()["access_token"]

        client.cookies["access_token"] = token
        response = client.get("/auth/me/")
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"

    def test_me_unauthenticated(self, client):
        response = client.get("/auth/me/")
        assert response.status_code == 401

    def test_logout(self, client):
        response = client.post("/auth/logout/")
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out"
