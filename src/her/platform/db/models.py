from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Enum, JSON, ForeignKey, Text
from datetime import datetime

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id:       Mapped[str] = mapped_column(String, primary_key=True)
    phone:    Mapped[str | None]
    created:  Mapped[datetime] = mapped_column(default=datetime.utcnow)
    meta:     Mapped[dict] = mapped_column(JSON, default=dict)

class Conversation(Base):
    __tablename__ = "conversations"
    id:        Mapped[str] = mapped_column(String, primary_key=True)
    user_id:   Mapped[str] = mapped_column(ForeignKey("users.id"))
    channel:   Mapped[str] = mapped_column(Enum("phone", "browser", "sms"))
    flow:      Mapped[str]
    started:   Mapped[datetime] = mapped_column(default=datetime.utcnow)
    ended:     Mapped[datetime | None]
    transcript:Mapped[str | None] = mapped_column(Text)
    meta:      Mapped[dict] = mapped_column(JSON, default=dict)
