import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class LocationType:
    """Location type constants for warehouse hierarchy."""

    WAREHOUSE = "warehouse"
    ROW = "row"
    BAY = "bay"
    LEVEL = "level"
    POSITION = "position"

    # All valid types
    ALL = [WAREHOUSE, ROW, BAY, LEVEL, POSITION]

    # Hierarchy order (parent -> child)
    HIERARCHY = {
        WAREHOUSE: ROW,
        ROW: BAY,
        BAY: LEVEL,
        LEVEL: POSITION,
        POSITION: None,
    }

    # Display names
    DISPLAY_NAMES = {
        WAREHOUSE: "Warehouse",
        ROW: "Row",
        BAY: "Bay",
        LEVEL: "Level",
        POSITION: "Position",
    }


class Location(Base):
    __tablename__ = "locations"

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
    # Hierarchy fields
    location_type = Column(
        String(20),
        nullable=False,
        default=LocationType.WAREHOUSE,
        server_default=LocationType.WAREHOUSE,
    )
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Basic info
    name = Column(String(255), index=True, nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    address = Column(String(500), nullable=True)  # Primarily for warehouses

    # Storage/organization
    barcode = Column(String(100), nullable=True)
    capacity = Column(Integer, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit fields
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
        Index("ix_locations_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_locations_tenant_active", "tenant_id", "is_active"),
    )

    # Relationships
    tenant = relationship("Tenant", backref="locations")
    parent = relationship(
        "Location",
        remote_side=[id],
        backref="children",
        foreign_keys=[parent_id],
    )
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_locations"
    )
    updater = relationship(
        "User", foreign_keys=[updated_by], backref="updated_locations"
    )

    @property
    def full_path(self) -> str:
        """Get the full hierarchical path of this location."""
        parts = [self.code]
        current = self.parent
        while current:
            parts.insert(0, current.code)
            current = current.parent
        return " > ".join(parts)

    @property
    def allowed_child_type(self) -> str | None:
        """Get the allowed child location type for this location."""
        return LocationType.HIERARCHY.get(self.location_type)
