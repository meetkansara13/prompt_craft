"""
tests/conftest.py
==================
Shared pytest fixtures available to all tests.
"""

import pytest
from app import create_app
from config.settings import TestingConfig


@pytest.fixture
def app():
    """Create a test Flask app with TestingConfig."""
    return create_app(TestingConfig())


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def app_ctx(app):
    """Push an application context for tests that need it."""
    with app.app_context():
        yield app


@pytest.fixture
def session_with_key(client):
    """Test client with a fake API key already set in session."""
    with client.session_transaction() as sess:
        sess["api_key"] = "gsk_fake-key-for-testing"
    return client
