import pytest
import os


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """
    Ensures tests never accidentally depend on your real .env file or make
    real API calls if OPENAI_API_KEY happens to be unset in the test environment.
    autouse=True means this runs for every test automatically, no need to
    request it explicitly in each test function.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")  # keep test output quiet