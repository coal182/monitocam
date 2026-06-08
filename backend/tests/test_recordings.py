import os
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ.setdefault("AUTH_USERNAME", "testuser")
os.environ.setdefault("AUTH_PASSWORD", "testpass")


@pytest.fixture
def auth_client(client):
    login_response = client.post(
        "/auth/login/",
        {"username": "testuser", "password": "testpass"},
        content_type="application/json",
    )
    token = login_response.json()["access_token"]
    client.cookies.set("access_token", token)
    return client


@pytest.mark.django_db
class TestRecordings:
    def test_list_recordings_empty(self, auth_client):
        response = auth_client.get("/recordings/")
        assert response.status_code == 200

    def test_unauthorized_access(self, client):
        response = client.get("/recordings/")
        assert response.status_code == 401
