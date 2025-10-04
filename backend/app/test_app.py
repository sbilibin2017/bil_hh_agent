from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

from backend.app.app import (
    Config,
    create_app,
    load_config_from_env_file,
    parse_env_file_arg,
    run_uvicorn,
)


# --------------------------
# parse_env_file_arg
# --------------------------
def test_parse_env_file_arg(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--env-file", "custom.env"])
    args = parse_env_file_arg()
    assert args.env_file == "custom.env"


# --------------------------
# load_config_from_env_file
# --------------------------
def test_load_config_from_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("HH_API_KEY=fake\nCHATGPT_API_KEY=fake\nJWT_SECRET=secret\n")
    cfg = load_config_from_env_file(str(env_file))
    assert cfg.HH_API_KEY == "fake"
    assert cfg.JWT_SECRET == "secret"


def test_load_config_file_not_found(tmp_path):
    env_file = tmp_path / "missing.env"
    with pytest.raises(FileNotFoundError):
        load_config_from_env_file(str(env_file))


# --------------------------
# Fixtures for create_app
# --------------------------
@pytest.fixture
def dummy_config():
    return Config()


@pytest.fixture
def patched_db_and_auth(monkeypatch):
    """Patch DB, repositories, and auth service to avoid real connections."""
    # Patch db module
    monkeypatch.setattr("backend.app.app.db", MagicMock())
    from backend.app.app import db as main_db

    class DummyDBContext:
        def transaction(self, func):
            return func

    main_db.db_context = DummyDBContext()
    main_db.engine = MagicMock()
    main_db.session_factory = MagicMock()

    # Patch user repository and auth service
    from backend.app.app import auth_svc, user_repo

    user_repo.user_repository = MagicMock()
    auth_svc.auth_service = MagicMock()


# --------------------------
# create_app
# --------------------------
def test_create_app_returns_fastapi(dummy_config, patched_db_and_auth):
    """Test that create_app returns a FastAPI instance with correct attributes."""
    app = create_app(dummy_config)
    assert isinstance(app, FastAPI)


# --------------------------
# run_uvicorn
# --------------------------
def test_run_uvicorn(monkeypatch, dummy_config):
    mock_run = MagicMock()
    monkeypatch.setattr("backend.app.app.uvicorn.run", mock_run)
    app = MagicMock()
    run_uvicorn(app, dummy_config)
    mock_run.assert_called_once_with(
        app,
        host=dummy_config.HOST,
        port=dummy_config.PORT,
        log_level=dummy_config.LOG_LEVEL.lower(),
        reload=dummy_config.DEBUG and dummy_config.WORKERS == 1,
        workers=dummy_config.WORKERS,
    )
