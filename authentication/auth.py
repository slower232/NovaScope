import re
from authentication.password_security import hash_password, verify_password
from database import repositories as repo

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


def register(username: str, password: str, role: str = "farmer", language: str = "es"):
    if not USERNAME_RE.match(username):
        raise ValueError("invalid_username")
    if role not in ("farmer", "advisor"):
        raise ValueError("invalid_role")
    if repo.get_user_by_name(username):
        raise ValueError("username_taken")
    return repo.create_user(username, hash_password(password), role, language)


def create_first_admin(username: str, password: str):
    """Solo permitido si no existe ningún usuario. Sin credenciales por defecto."""
    if repo.count_users() > 0:
        raise PermissionError("admin_already_configured")
    if not USERNAME_RE.match(username):
        raise ValueError("invalid_username")
    return repo.create_user(username, hash_password(password), "admin")


def login(username: str, password: str):
    u = repo.get_user_by_name(username)
    if u and verify_password(password, u.password_hash):
        return u
    return None
