from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class RoomRow(Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    revision: Mapped[int] = mapped_column(default=1)


class EventRow(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    kind: Mapped[str] = mapped_column(String(30))
    scope: Mapped[str] = mapped_column(String(20))
    scope_id: Mapped[int | None]
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id"))
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(default=1)


class CeremonyRow(Base):
    __tablename__ = "ceremonies"
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    service_key: Mapped[str] = mapped_column(String(80), unique=True)
    program: Mapped[dict[str, object]] = mapped_column(JSON)
    timer: Mapped[dict[str, object]] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(default=1)


class PrayerRow(Base):
    __tablename__ = "prayers"
    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(240))
    details: Mapped[str] = mapped_column(Text)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")


class SlotRow(Base):
    __tablename__ = "service_slots"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    ministry_id: Mapped[int] = mapped_column(ForeignKey("ministries.id"))
    title: Mapped[str] = mapped_column(String(120))
    capacity: Mapped[int]
    revision: Mapped[int] = mapped_column(default=1)


class SignupRow(Base):
    __tablename__ = "service_signups"
    slot_id: Mapped[int] = mapped_column(ForeignKey("service_slots.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="active")


class PreparationRow(Base):
    __tablename__ = "event_preparations"
    id: Mapped[int] = mapped_column(primary_key=True)
    ministry_id: Mapped[int] = mapped_column(ForeignKey("ministries.id"))
    title: Mapped[str] = mapped_column(String(240))
    kind: Mapped[str] = mapped_column(String(10))
    steps: Mapped[list[str]] = mapped_column(JSON)
    completed: Mapped[list[int]] = mapped_column(JSON)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
