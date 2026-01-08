"""
Supplier model for vendor/supplier management.
"""

import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Supplier(Base):
    """
    Supplier model for managing vendor/supplier information.

    Centralizes supplier data for reuse across multiple purchase orders,
    enables supplier rating, and supports integrated sourcing workflows.
    """

    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Supplier identification
    name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)

    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Address fields
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Additional information
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
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
    tenant = relationship("Tenant", backref="suppliers")
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        backref="suppliers_created",
    )
    updated_by_user = relationship(
        "User",
        foreign_keys=[updated_by],
        backref="suppliers_updated",
    )
    purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="supplier",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Supplier(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"
        )
