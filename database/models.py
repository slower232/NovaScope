"""Modelos SQLAlchemy 2.0. (Roles se modelan como columna 'role' de User en esta fase.)"""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(16), default="farmer")  # farmer | advisor | admin
    language: Mapped[str] = mapped_column(String(2), default="es")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    farms: Mapped[list["Farm"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Farm(Base):
    __tablename__ = "farms"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    crop_id: Mapped[str] = mapped_column(String(40))
    irrigated: Mapped[bool] = mapped_column(Boolean, default=False)
    area_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_texture: Mapped[str | None] = mapped_column(String(40), nullable=True)
    soil_ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    sowing_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    owner: Mapped[User] = relationship(back_populates="farms")
    boundary: Mapped["FarmBoundary | None"] = relationship(back_populates="farm", cascade="all, delete-orphan", uselist=False)


class FarmBoundary(Base):
    __tablename__ = "farm_boundaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), unique=True)
    geojson: Mapped[str] = mapped_column(Text)
    farm: Mapped[Farm] = relationship(back_populates="boundary")


class ApiCache(Base):
    """Caché de respuestas de APIs externas (evita solicitudes repetidas)."""
    __tablename__ = "api_cache"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    source: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class RotationPlan(Base):
    __tablename__ = "rotation_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    weights_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)


class Simulation(Base):
    __tablename__ = "simulations"
    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    params_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)


class RiskAlertRecord(Base):
    __tablename__ = "risk_alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    risk_key: Mapped[str] = mapped_column(String(40))
    level: Mapped[str] = mapped_column(String(8))
    params_json: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80))
