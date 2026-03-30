"""
SQLAlchemy tükörmodellek a Django által létrehozott táblákhoz.
FastAPI csak olvas ezekből (kivéve metrics táblákat).
"""
from datetime import datetime, date
from uuid import UUID
from sqlalchemy import (
    JSON, String, Boolean, Text, Integer, BigInteger,
    TIMESTAMP, Date, ForeignKey, CHAR, ARRAY, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Client(Base):
    __tablename__ = "tokens_client"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    tokens: Mapped[list["ApiToken"]] = relationship("ApiToken", back_populates="client")


class ApiToken(Base):
    __tablename__ = "tokens_apitoken"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    client_id: Mapped[UUID] = mapped_column(ForeignKey("tokens_client.id"))
    token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    token_prefix: Mapped[str] = mapped_column(CHAR(8))
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean)
    revoked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String))
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_limit_per_day: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_used_ip: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    client: Mapped["Client"] = relationship("Client", back_populates="tokens")


class Language(Base):
    __tablename__ = "translations_language"

    code: Mapped[str] = mapped_column(CHAR(5), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean)
    is_default: Mapped[bool] = mapped_column(Boolean)


class TranslationNamespace(Base):
    __tablename__ = "translations_namespace"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean)
    keys: Mapped[list["TranslationKey"]] = relationship("TranslationKey", back_populates="namespace")


class TranslationKey(Base):
    __tablename__ = "translations_translationkey"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    namespace_id: Mapped[UUID] = mapped_column(ForeignKey("translations_namespace.id"))
    key: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean)
    namespace: Mapped["TranslationNamespace"] = relationship("TranslationNamespace", back_populates="keys")
    translations: Mapped[list["Translation"]] = relationship("Translation", back_populates="translation_key")


class Translation(Base):
    __tablename__ = "translations_translation"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    key_id: Mapped[UUID] = mapped_column(ForeignKey("translations_translationkey.id"))
    # Django ForeignKey -> language_id oszlopnév a DB-ben
    language_id: Mapped[str] = mapped_column(CHAR(5), ForeignKey("translations_language.code"))
    value: Mapped[str] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean)
    synced_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    translation_key: Mapped["TranslationKey"] = relationship("TranslationKey", back_populates="translations")


# ── FastAPI által írt táblák ─────────────────────────────────────────────────

class TokenUsageDaily(Base):
    __tablename__ = "metrics_tokenusagedaily"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    token_id: Mapped[UUID] = mapped_column(ForeignKey("tokens_apitoken.id"))
    date: Mapped[date] = mapped_column(Date)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    bytes_sent: Mapped[int] = mapped_column(BigInteger, default=0)
    bytes_received: Mapped[int] = mapped_column(BigInteger, default=0)
    __table_args__ = (UniqueConstraint("token_id", "date"),)


class SyncLog(Base):
    __tablename__ = "metrics_synclog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="running")
    keys_added: Mapped[int] = mapped_column(Integer, default=0)
    keys_updated: Mapped[int] = mapped_column(Integer, default=0)
    keys_removed: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class AuthFailure(Base):
    __tablename__ = "metrics_authfailure"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    token_prefix: Mapped[str | None] = mapped_column(CHAR(8), nullable=True)
    failure_reason: Mapped[str] = mapped_column(String(50))
    client_ip: Mapped[str] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
