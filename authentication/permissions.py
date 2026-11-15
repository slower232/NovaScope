ROLES = ("farmer", "advisor", "admin")
PERMS = {
    "farmer": {"farm:write", "farm:read_own", "simulate", "report"},
    "advisor": {"farm:read_all", "simulate", "report"},
    "admin": {"farm:read_all", "farm:write", "users:manage", "catalog:manage", "simulate", "report"},
}


def can(role: str, perm: str) -> bool:
    return perm in PERMS.get(role, set())
