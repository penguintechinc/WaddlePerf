"""Shared pytest fixtures for containerClient unit tests."""
import sys
from unittest.mock import MagicMock

# Mock missing external modules
sys.modules['penguintechinc_utils'] = MagicMock()
sys.modules['penguintechinc_utils.logging'] = MagicMock()
sys.modules['penguin_libs'] = MagicMock()

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_env(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv('MANAGER_URL', 'http://localhost:5000')
    monkeypatch.setenv('MANAGER_API_KEY', 'test-api-key')
    monkeypatch.setenv('DEVICE_NAME', 'test-device')
