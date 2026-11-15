import os, tempfile, pytest
pytest.importorskip("sqlalchemy")
from authentication.password_security import hash_password, verify_password


def test_password_hash_never_plaintext():
    h = hash_password("contraseña-segura-1")
    assert "contraseña" not in h and verify_password("contraseña-segura-1", h) and not verify_password("otra", h)
    with pytest.raises(ValueError):
        hash_password("corta")


def test_db_roundtrip_and_ownership(tmp_path):
    from database.connection import reset_engine
    from database.initialization import init_db
    from database import repositories as repo
    from authentication import auth
    reset_engine(str(tmp_path / "t.db")); init_db()
    admin = auth.create_first_admin("admin_test", "clave-larga-123")
    with pytest.raises(PermissionError):
        auth.create_first_admin("otro", "clave-larga-123")
    u1 = auth.register("agri1", "clave-larga-123"); u2 = auth.register("agri2", "clave-larga-123")
    f = repo.create_farm(u1.id, dict(name="P1", lat=28.6, lon=-106.1, crop_id="maiz"))
    assert repo.get_farm(u1, f.id) is not None and repo.get_farm(u2, f.id) is None
    assert auth.login("agri1", "clave-larga-123") and not auth.login("agri1", "mal")
