from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uid() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "mt_users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    username: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(40))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(12), default="user")
    avatar_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    instagram: Mapped[str] = mapped_column(String(30), default="")
    snapchat: Mapped[str] = mapped_column(String(30), default="")
    twitter: Mapped[str] = mapped_column(String(15), default="")
    bot_name: Mapped[str] = mapped_column(String(40), default="رفيق الكتابة")
    bot_avatar_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        CheckConstraint("username = lower(username)", name="ck_mt_username_normalized"),
    )


class LoginSession(Base):
    __tablename__ = "mt_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    csrf_token: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Media(Base):
    __tablename__ = "mt_media"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(12))
    data: Mapped[bytes] = mapped_column(LargeBinary)
    etag: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class Follow(Base):
    __tablename__ = "mt_follows"
    follower_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), primary_key=True
    )
    followed_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class Block(Base):
    __tablename__ = "mt_blocks"
    blocker_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), primary_key=True
    )
    blocked_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class Message(Base):
    __tablename__ = "mt_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    recipient_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    media_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    challenge_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    __table_args__ = (Index("ix_mt_message_pair", "sender_id", "recipient_id", "id"),)


class Notification(Base):
    __tablename__ = "mt_notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[str | None] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(24))
    body: Mapped[str] = mapped_column(String(240), default="")
    resource: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Challenge(Base):
    __tablename__ = "mt_challenges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    invite_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    visibility: Mapped[str] = mapped_column(String(12), default="private")
    game: Mapped[str] = mapped_column(String(12))
    difficulty: Mapped[str] = mapped_column(String(12))
    language: Mapped[str] = mapped_column(String(2))
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic: Mapped[str] = mapped_column(
        String(24), default="mixed", server_default="mixed"
    )
    max_players: Mapped[int] = mapped_column(Integer, default=8)
    round_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    current_round: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    judge_mode: Mapped[str] = mapped_column(
        String(16), default="points", server_default="points"
    )
    event_kind: Mapped[str] = mapped_column(
        String(16), default="challenge", server_default="challenge"
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(12), default="lobby")
    target: Mapped[str] = mapped_column(Text, default="")
    display: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PracticeRound(Base):
    __tablename__ = "mt_rounds"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    expected: Mapped[str] = mapped_column(Text)
    display: Mapped[str] = mapped_column(Text)
    game: Mapped[str] = mapped_column(String(12))
    difficulty: Mapped[str] = mapped_column(String(12))
    language: Mapped[str] = mapped_column(String(2))
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    challenge_id: Mapped[str | None] = mapped_column(
        ForeignKey("mt_challenges.id", ondelete="CASCADE"), nullable=True, index=True
    )
    challenge_round: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    topic: Mapped[str] = mapped_column(
        String(24), default="mixed", server_default="mixed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)


class Attempt(Base):
    __tablename__ = "mt_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    round_id: Mapped[str] = mapped_column(
        ForeignKey("mt_rounds.id", ondelete="CASCADE"), unique=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    game: Mapped[str] = mapped_column(String(12))
    difficulty: Mapped[str] = mapped_column(String(12))
    language: Mapped[str] = mapped_column(String(2))
    points: Mapped[int] = mapped_column(Integer)
    penalty: Mapped[int] = mapped_column(Integer)
    accuracy: Mapped[float] = mapped_column(Float)
    wpm: Mapped[float] = mapped_column(Float)
    elapsed_seconds: Mapped[float] = mapped_column(Float)
    correct_characters: Mapped[int] = mapped_column(Integer)
    error_count: Mapped[int] = mapped_column(Integer)
    eligible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (Index("ix_mt_attempt_user_created", "user_id", "created_at"),)


class ChallengeParticipant(Base):
    __tablename__ = "mt_challenge_participants"
    challenge_id: Mapped[str] = mapped_column(
        ForeignKey("mt_challenges.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), primary_key=True
    )
    round_id: Mapped[str | None] = mapped_column(
        ForeignKey("mt_rounds.id", ondelete="CASCADE"), nullable=True, unique=True
    )
    attempt_id: Mapped[int | None] = mapped_column(
        ForeignKey("mt_attempts.id", ondelete="CASCADE"), nullable=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class GameSuggestion(Base):
    __tablename__ = "mt_game_suggestions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("mt_users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), default="pending")
    admin_note: Mapped[str] = mapped_column(String(500), default="")
    reviewed_by: Mapped[str | None] = mapped_column(
        ForeignKey("mt_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
