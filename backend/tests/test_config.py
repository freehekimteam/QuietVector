"""
Tests for configuration and settings
"""
import pytest
from pathlib import Path
from pydantic import SecretStr

from app.core.config import Settings


def test_settings_defaults():
    """Test default settings values"""
    settings = Settings()
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8090
    assert settings.qdrant_host == "localhost"
    assert settings.qdrant_port == 6333
    assert settings.rate_limit_per_minute == 60
    assert settings.max_body_size_bytes == 1048576


def test_settings_env_override(monkeypatch):
    """Test that environment variables override defaults"""
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "120")

    settings = Settings()
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 9000
    assert settings.rate_limit_per_minute == 120


def test_settings_api_port_validation():
    """Test API port validation"""
    # Port too low
    with pytest.raises(Exception):  # Pydantic ValidationError
        Settings(api_port=1023)

    # Port too high
    with pytest.raises(Exception):
        Settings(api_port=70000)

    # Valid ports
    settings = Settings(api_port=8080)
    assert settings.api_port == 8080


def test_settings_qdrant_api_key_from_env(monkeypatch):
    """Test Qdrant API key from environment"""
    monkeypatch.setenv("QDRANT_API_KEY", "test_key_123")

    settings = Settings()
    assert settings.get_qdrant_api_key() == "test_key_123"


def test_settings_qdrant_api_key_from_file(tmp_path: Path):
    """Test Qdrant API key from file (preferred method)"""
    key_file = tmp_path / "qdrant_key.txt"
    key_file.write_text("file_key_456", encoding="utf-8")

    settings = Settings(qdrant_api_key_file=key_file)
    # File should take precedence
    assert settings.get_qdrant_api_key() == "file_key_456"


def test_settings_qdrant_api_key_file_precedence(tmp_path: Path):
    """Test that key file takes precedence over env var"""
    key_file = tmp_path / "qdrant_key.txt"
    key_file.write_text("file_key", encoding="utf-8")

    settings = Settings(
        qdrant_api_key=SecretStr("env_key"),
        qdrant_api_key_file=key_file
    )
    # File should win
    assert settings.get_qdrant_api_key() == "file_key"


def test_settings_jwt_secret():
    """Test JWT secret retrieval"""
    settings = Settings(jwt_secret=SecretStr("my_secret_key"))
    assert settings.get_jwt_secret() == "my_secret_key"


def test_settings_ops_apply_disabled_by_default():
    """Test that ops_apply is disabled by default"""
    settings = Settings()
    assert settings.enable_ops_apply is False


def test_settings_ops_apply_modes():
    """Test ops_apply mode validation"""
    settings = Settings(
        enable_ops_apply=True,
        ops_apply_mode="docker_compose"
    )
    assert settings.ops_apply_mode == "docker_compose"

    settings = Settings(
        enable_ops_apply=True,
        ops_apply_mode="systemctl"
    )
    assert settings.ops_apply_mode == "systemctl"


def test_settings_use_https_property():
    """Test use_https property based on port"""
    settings = Settings(qdrant_port=443)
    assert settings.use_https is True

    settings = Settings(qdrant_port=6333)
    assert settings.use_https is False


def test_settings_token_expire_validation():
    """Test token expiration time validation"""
    # Too short
    with pytest.raises(Exception):
        Settings(token_expire_minutes=1)

    # Too long (>24 hours)
    with pytest.raises(Exception):
        Settings(token_expire_minutes=2000)

    # Valid
    settings = Settings(token_expire_minutes=120)
    assert settings.token_expire_minutes == 120


def test_settings_rate_limit_validation():
    """Test rate limit validation"""
    # Too low
    with pytest.raises(Exception):
        Settings(rate_limit_per_minute=0)

    # Too high
    with pytest.raises(Exception):
        Settings(rate_limit_per_minute=20000)

    # Valid
    settings = Settings(rate_limit_per_minute=100)
    assert settings.rate_limit_per_minute == 100


def test_settings_body_size_limit_validation():
    """Test body size limit validation"""
    # Too small
    with pytest.raises(Exception):
        Settings(max_body_size_bytes=500)

    # Too large (>10MB)
    with pytest.raises(Exception):
        Settings(max_body_size_bytes=20_000_000)

    # Valid
    settings = Settings(max_body_size_bytes=2_000_000)
    assert settings.max_body_size_bytes == 2_000_000
