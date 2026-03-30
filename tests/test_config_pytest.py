import os
import pytest

import config


def test_get_env_returns_value(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "value")
    assert config.get_env("TEST_KEY") == "value"


def test_get_env_default():
    assert config.get_env("NO_SUCH_KEY", default="d") == "d"
