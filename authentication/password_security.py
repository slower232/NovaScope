"""Hash de contraseñas con scrypt (stdlib). Formato: scrypt$N$r$p$salt_hex$hash_hex."""
import hashlib, hmac, os

N, R, P = 2 ** 14, 8, 1


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("La contraseña debe tener al menos 10 caracteres")
    salt = os.urandom(16)
    h = hashlib.scrypt(password.encode(), salt=salt, n=N, r=R, p=P, dklen=32)
    return f"scrypt${N}${R}${P}${salt.hex()}${h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, h = stored.split("$")
        calc = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(calc.hex(), h)
    except Exception:
        return False
