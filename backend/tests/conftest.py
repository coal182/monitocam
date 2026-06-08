import os

import pytest
from django.test import RequestFactory


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")


@pytest.fixture
def request_factory():
    return RequestFactory()
