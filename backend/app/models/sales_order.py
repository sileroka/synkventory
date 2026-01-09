"""
Sales order models for outbound fulfillment.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class SalesOrderStatus(str, Enum):
    """Status values for sales orders."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PICKED = "picked"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class SalesOrderPriority(str, Enum):
    """Priority levels for sales orders."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class SalesOrder(Base):
    """Sales order representing outbound customer fulfillment."""

    __tablename__ = "sales_orders"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "order_number",
            name="uq_sales_orders_tenant_order_number",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_number = Column(String(50), nullable=False, index=True)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = Column(
        SQLEnum(
            SalesOrderStatus,
            name="sales_order_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=SalesOrderStatus.DRAFT,
        index=True,
    )
    priority = Column(
        SQLEnum(
            SalesOrderPriority,
            name="sales_order_priority",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=SalesOrderPriority.NORMAL,
    )

    order_date = Column(DateTime(timezone=True), nullable=True)
    expected_ship_date = Column(DateTime(timezone=True), nullable=True)
    shipped_date = Column(DateTime(timezone=True), nullable=True)
    cancelled_date = Column(DateTime(timezone=True), nullable=True)

    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    shipping_cost = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)

    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
    tenant = relationship("Tenant", backref="sales_orders")
    customer = relationship("Customer", back_populates="sales_orders")
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_sales_orders",
    )
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    line_items = relationship(
        "SalesOrderLineItem",
        back_populates="sales_order",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<SalesOrder {self.order_number} - {self.status.value}>"


class SalesOrderLineItem(Base):
    """Line item belonging to a sales order."""

    __tablename__ = "sales_order_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sales_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sales_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    quantity_ordered = Column(Integer, nullable=False, default=1)
    quantity_shipped = Column(Integer, nullable=False, default=0)

    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    line_total = Column(Numeric(12, 2), nullable=False, default=0)

    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    tenant = relationship("Tenant")
    sales_order = relationship("SalesOrder", back_populates="line_items")
    item = relationship("InventoryItem", backref="sales_order_line_items")

    def __repr__(self):
        return f"<SalesOrderLineItem {self.item_id} x{self.quantity_ordered}>"

    @property
    def quantity_remaining(self) -> int:
        """Calculate remaining quantity to ship."""
        return max(0, self.quantity_ordered - self.quantity_shipped)

    def calculate_line_total(self) -> None:
        """Calculate line total from quantity and price."""
        self.line_total = self.unit_price * self.quantity_ordered
