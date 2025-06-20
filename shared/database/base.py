# shared/database/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, func
from datetime import datetime
from uuid import UUID, uuid4

class Base(DeclarativeBase):
    pass

class BaseTable:
    """Base mixin for all tables"""
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )

class OrganizationMixin:
    """Mixin for multi-tenant tables"""
    organization_id: Mapped[UUID] = mapped_column(nullable=False, index=True)


