from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tracked_terms = relationship("TrackedTerm", back_populates="user", cascade="all, delete-orphan")


class TrackedTerm(Base):
    __tablename__ = "tracked_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    term: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tracked_terms")


class CauseList(Base):
    __tablename__ = "cause_lists"
    __table_args__ = (UniqueConstraint("list_date", "source_url", name="uq_list_date_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items = relationship("CauseListItem", back_populates="cause_list", cascade="all, delete-orphan")


class CauseListItem(Base):
    __tablename__ = "cause_list_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cause_list_id: Mapped[int] = mapped_column(ForeignKey("cause_lists.id"), nullable=False)
    court_no: Mapped[str] = mapped_column(String(100), default="")
    item_no: Mapped[str] = mapped_column(String(100), default="")
    case_no: Mapped[str] = mapped_column(String(255), default="")
    parties: Mapped[str] = mapped_column(Text, default="")
    advocates: Mapped[str] = mapped_column(Text, default="")
    stage: Mapped[str] = mapped_column(String(255), default="")
    full_text: Mapped[str] = mapped_column(Text, default="")

    cause_list = relationship("CauseList", back_populates="items")
    matches = relationship("Match", back_populates="item", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("cause_list_items.id"), nullable=False)
    matched_term: Mapped[str] = mapped_column(String(255), nullable=False)
    matched_on: Mapped[str] = mapped_column(String(64), default="COUNSEL")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    item = relationship("CauseListItem", back_populates="matches")
