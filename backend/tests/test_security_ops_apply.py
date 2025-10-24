from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from argon2 import PasswordHasher

from app.main import app
from app.routes import security as sec


def _set_admin_password(pw: str) -> None:
    ph = PasswordHasher()
    sec.settings.admin_password_hash = ph.hash(pw)


def test_ops_apply_dry_run_compose(tmp_path: Path):
    # configure settings for test
    _set_admin_password('pw')
    sec.settings.enable_ops_apply = True
    sec.settings.ops_apply_mode = 'docker_compose'
    compose = tmp_path / 'compose.yml'
    compose.write_text('version: "3"\n', encoding='utf-8')
    sec.settings.ops_apply_compose_file = compose
    sec.settings.ops_apply_service = 'qdrant'

    c = TestClient(app)
    r = c.post('/api/security/ops_apply', json={
        'admin_password': 'pw',
        'dry_run': True,
    }, headers={'authorization': 'Bearer dummy'})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['executed'] is False
    assert 'docker' in data['command'][0]


def test_ops_apply_exec_compose(tmp_path: Path):
    _set_admin_password('pw')
    sec.settings.enable_ops_apply = True
    sec.settings.ops_apply_mode = 'docker_compose'
    compose = tmp_path / 'compose.yml'
    compose.write_text('version: "3"\n', encoding='utf-8')
    sec.settings.ops_apply_compose_file = compose
    sec.settings.ops_apply_service = 'qdrant'

    with patch('app.routes.security.subprocess.run') as run:
        run.return_value = SimpleNamespace(returncode=0, stdout='ok', stderr='')
        c = TestClient(app)
        r = c.post('/api/security/ops_apply', json={'admin_password': 'pw', 'dry_run': False}, headers={'authorization': 'Bearer dummy'})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data['executed'] is True
        assert data['rc'] == 0
        run.assert_called_once()

