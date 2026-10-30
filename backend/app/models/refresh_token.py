"""Refresh tokens persistidos (solo hash) para renovación de sesión JWT."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Nunca se guarda el token en claro: solo SHA-256 del valor
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_refresh_token_usuario", "usuario_id"),)

    usuario = relationship("User", foreign_keys=[usuario_id])
