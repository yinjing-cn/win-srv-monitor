"""Shared pytest fixtures."""

import os
import sys
import pytest
import shutil
import tempfile
from pathlib import Path

# Ensure mock mode for all tests
os.environ["MOCK_MODE"] = "1"

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitor.config import AppConfig
from monitor.store import DataStore
from monitor.app import create_app


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory."""
    d = tmp_path / "test_data"
    d.mkdir()
    return str(d)


@pytest.fixture
def config():
    """Provide a test configuration."""
    return AppConfig(
        mock_mode=True,
        flask_host="127.0.0.1",
        flask_port=5555,
        collect_interval=999,
        data_dir="data",
    )


@pytest.fixture
def store(tmp_data_dir):
    """Provide a fresh DataStore."""
    return DataStore(data_dir=tmp_data_dir, max_history=50)


@pytest.fixture
def app(config):
    """Provide a test Flask app."""
    config_mock = AppConfig(
        mock_mode=True,
        collect_interval=999,
        data_dir="data",
    )
    application = create_app(config_mock)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    """Provide a Flask test client."""
    return app.test_client()


# Updated: 2026-09-07
