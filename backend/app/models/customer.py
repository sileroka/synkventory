"""
Customer model for managing outbound sales relationships.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Customer(Base):
    """Customer model supporting sales orders and fulfillment workflows."""

    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Customer identity and contact
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Addresses
    shipping_address = Column(JSONB, nullable=True)
    billing_address = Column(JSONB, nullable=True)

    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    tenant = relationship("Tenant", backref="customers")
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        backref="customers_created",
    )
    updated_by_user = relationship(
        "User",
        foreign_keys=[updated_by],
        backref="customers_updated",
    )
    sales_orders = relationship(
        "SalesOrder",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"
