"""Acceso a datos con consultas parametrizadas (ORM). Control de propiedad en cada consulta."""
import json
from sqlalchemy import select
from database.connection import get_session
from database.models import Farm, FarmBoundary, RotationPlan, Simulation, User


def count_users() -> int:
    with get_session() as s:
        return len(s.scalars(select(User.id)).all())


def create_user(username, password_hash, role="farmer", language="es") -> User:
    with get_session() as s:
        u = User(username=username, password_hash=password_hash, role=role, language=language)
        s.add(u); s.commit()
        return u


def get_user_by_name(username: str):
    with get_session() as s:
        return s.scalar(select(User).where(User.username == username))


def create_farm(owner_id: int, data: dict, geojson: dict | None = None) -> Farm:
    with get_session() as s:
        f = Farm(owner_id=owner_id, **data)
        if geojson:
            f.boundary = FarmBoundary(geojson=json.dumps(geojson))
        s.add(f); s.commit()
        return f


def list_farms(user) -> list[Farm]:
    with get_session() as s:
        q = select(Farm) if user.role in ("admin", "advisor") else select(Farm).where(Farm.owner_id == user.id)
        return list(s.scalars(q.order_by(Farm.id)))


def get_farm(user, farm_id: int):
    with get_session() as s:
        f = s.get(Farm, farm_id)
        if f is None or (f.owner_id != user.id and user.role not in ("admin", "advisor")):
            return None
        return f


def delete_farm(user, farm_id: int) -> bool:
    with get_session() as s:
        f = s.get(Farm, farm_id)
        if f is None or (f.owner_id != user.id and user.role != "admin"):
            return False
        s.delete(f); s.commit()
        return True


def save_rotation(farm_id: int, weights: dict, result: dict):
    with get_session() as s:
        s.add(RotationPlan(farm_id=farm_id, weights_json=json.dumps(weights), result_json=json.dumps(result, default=str)))
        s.commit()


def save_simulation(farm_id: int, params: dict, result: dict):
    with get_session() as s:
        s.add(Simulation(farm_id=farm_id, params_json=json.dumps(params), result_json=json.dumps(result, default=str)))
        s.commit()
