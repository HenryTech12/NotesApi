# src/models/note.py
import uuid
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from src.database import Base

class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, server_default='[]')
    suggested_tags: Mapped[list[str]] = mapped_column(JSON, default=list, server_default='[]')
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    summary_generated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notes")

    __table_args__ = (
        Index("ix_notes_user_id", "user_id"),
        Index("ix_notes_created_at", "created_at"),
    )
