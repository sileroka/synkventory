import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), index=True, nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    updated_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Indexes for multi-tenancy queries
    __table_args__ = (
        Index("ix_categories_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_categories_tenant_active", "tenant_id", "is_active"),
        Index("ix_categories_tenant_parent", "tenant_id", "parent_id"),
    )

    # Self-referential relationships
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan"
    )

    # Tenant relationship
    tenant = relationship("Tenant", backref="categories")

    # User relationships
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_categories"
    )
    updater = relationship(
        "User", foreign_keys=[updated_by], backref="updated_categories"
    )
