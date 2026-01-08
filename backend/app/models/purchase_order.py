"""
Purchase Order model for procurement management.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Numeric,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class PurchaseOrderStatus(str, Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrderPriority(str, Enum):
    """Priority levels for purchase orders."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PurchaseOrder(Base):
    """
    Purchase Order model for tracking procurement of inventory items.

    A purchase order represents a request to purchase items from a supplier,
    typically triggered by low stock levels or manual reorder requests.
    """

    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Purchase order identification
    po_number = Column(String(50), nullable=False, index=True)

    # Supplier relationship (optional - legacy POs may have text-only supplier info)
    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Supplier information (stored as text for flexibility and backward compatibility)
    supplier_name = Column(String(255), nullable=True)
    supplier_contact = Column(String(255), nullable=True)
    supplier_email = Column(String(255), nullable=True)
    supplier_phone = Column(String(50), nullable=True)

    # Status and priority
    status = Column(
        SQLEnum(
            PurchaseOrderStatus,
            name="purchase_order_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )
    priority = Column(
        SQLEnum(
            PurchaseOrderPriority,
            name="purchase_order_priority",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=PurchaseOrderPriority.NORMAL,
    )

    # Dates
    order_date = Column(DateTime(timezone=True), nullable=True)
    expected_date = Column(DateTime(timezone=True), nullable=True)
    received_date = Column(DateTime(timezone=True), nullable=True)

    # Receiving location
    receiving_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Assigned/Requested by
    requested_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Notes and references
    notes = Column(Text, nullable=True)
    external_reference = Column(String(100), nullable=True)  # External PO number

    # Totals (calculated from line items)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    shipping_cost = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)

    # Auto-generated flag
    auto_generated = Column(Boolean, nullable=False, default=False)

    # Audit fields
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
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    tenant = relationship("Tenant", backref="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")
    receiving_location = relationship("Location", backref="purchase_orders")
    requested_by = relationship(
        "User", foreign_keys=[requested_by_id], backref="requested_purchase_orders"
    )
    approved_by = relationship(
        "User", foreign_keys=[approved_by_id], backref="approved_purchase_orders"
    )
    created_by_user = relationship(
        "User", foreign_keys=[created_by], backref="created_purchase_orders"
    )
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    line_items = relationship(
        "PurchaseOrderLineItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<PurchaseOrder {self.po_number} - {self.status.value}>"

    @property
    def is_overdue(self) -> bool:
        """Check if purchase order is overdue."""
        if not self.expected_date:
            return False
        if self.status in [PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CANCELLED]:
            return False
        return datetime.utcnow() > self.expected_date

    def calculate_totals(self) -> None:
        """Recalculate totals from line items."""
        self.subtotal = sum(
            (item.quantity_ordered * item.unit_price) for item in self.line_items
        )
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost

    @property
    def supplier_display_name(self) -> str | None:
        """Preferred supplier name: linked Supplier.name first, otherwise stored text."""
        if self.supplier and self.supplier.name:
            return self.supplier.name
        return self.supplier_name


class PurchaseOrderLineItem(Base):
    """
    Line item for a purchase order.

    Represents a single item being ordered with quantity and pricing.
    """

    __tablename__ = "purchase_order_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Parent purchase order
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The item being ordered
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Quantities
    quantity_ordered = Column(Integer, nullable=False, default=1)
    quantity_received = Column(Integer, nullable=False, default=0)

    # Pricing
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    line_total = Column(Numeric(12, 2), nullable=False, default=0)

    # Notes for this line item
    notes = Column(Text, nullable=True)

    # Audit fields
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
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")
    item = relationship("InventoryItem", backref="purchase_order_line_items")

    def __repr__(self):
        return f"<PurchaseOrderLineItem {self.item_id} x{self.quantity_ordered}>"

    @property
    def quantity_remaining(self) -> int:
        """Calculate remaining quantity to receive."""
        return max(0, self.quantity_ordered - self.quantity_received)

    def calculate_line_total(self) -> None:
        """Calculate line total from quantity and price."""
        self.line_total = Decimal(str(self.quantity_ordered)) * self.unit_price
