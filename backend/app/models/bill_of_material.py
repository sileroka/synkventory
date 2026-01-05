"""
Bill of Materials model for tracking item compositions.

A Bill of Material (BOM) defines how an assembly item is composed of
component items. Each BOM line specifies a component and its quantity
needed to build one unit of the parent assembly.
"""

import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class BillOfMaterial(Base):
    """
    Represents a component in a Bill of Materials.
    
    Each record links a parent (assembly) item to a component item,
    specifying how many units of the component are needed to build
    one unit of the parent.
    """
    __tablename__ = "bill_of_materials"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # The parent/assembly item that is being built
    parent_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # The component item used in the assembly
    component_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # How many units of the component are needed for one parent assembly
    quantity_required = Column(Integer, nullable=False, default=1)
    
    # Optional unit of measure (e.g., "pieces", "kg", "meters")
    unit_of_measure = Column(String(50), nullable=True, default="units")
    
    # Optional notes about this component in the assembly
    notes = Column(Text, nullable=True)
    
    # Display order for organizing components in the BOM list
    display_order = Column(Integer, nullable=True, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Indexes for multi-tenancy and common queries
    __table_args__ = (
        # Ensure unique parent-component combinations per tenant
        Index(
            "ix_bom_tenant_parent_component",
            "tenant_id",
            "parent_item_id",
            "component_item_id",
            unique=True,
        ),
        # For querying all components of a parent
        Index("ix_bom_parent_item", "parent_item_id"),
        # For querying where a component is used
        Index("ix_bom_component_item", "component_item_id"),
        # For tenant-scoped queries
        Index("ix_bom_tenant_id", "tenant_id"),
    )

    # Relationships
    tenant = relationship("Tenant", backref="bill_of_materials")
    parent_item = relationship(
        "InventoryItem",
        foreign_keys=[parent_item_id],
        backref="bom_components",  # Components that make up this item
    )
    component_item = relationship(
        "InventoryItem",
        foreign_keys=[component_item_id],
        backref="used_in_assemblies",  # Assemblies this item is used in
    )
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_bom_entries",
    )
    updater = relationship(
        "User",
        foreign_keys=[updated_by],
        backref="updated_bom_entries",
    )

    def __repr__(self):
        return f"<BillOfMaterial(parent={self.parent_item_id}, component={self.component_item_id}, qty={self.quantity_required})>"
