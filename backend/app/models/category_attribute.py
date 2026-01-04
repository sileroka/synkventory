"""
CategoryAttribute model for defining custom fields per category.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class CategoryAttribute(Base):
    """
    Defines custom attributes that can be added to inventory items.
    Attributes are scoped to a category - all items in a category
    share the same available custom attributes.
    """

    __tablename__ = "category_attributes"

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
    # Nullable for global attributes (apply to all categories)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Flag to indicate global attribute (applies to all items)
    is_global = Column(Boolean, default=False, nullable=False)

    # Attribute definition
    name = Column(String(100), nullable=False)  # Display name
    key = Column(String(50), nullable=False)  # Machine-readable key
    attribute_type = Column(
        String(20), nullable=False, default="text"
    )  # text, number, boolean, date, select
    description = Column(String(500), nullable=True)

    # For select type - comma-separated options
    options = Column(String(1000), nullable=True)

    # Validation
    is_required = Column(Boolean, default=False, nullable=False)
    default_value = Column(String(500), nullable=True)

    # Display
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_category_attributes_tenant_category", "tenant_id", "category_id"),
        Index("ix_category_attributes_tenant_global", "tenant_id", "is_global"),
        # Partial unique index for category-specific attributes
        Index(
            "ix_category_attributes_category_key",
            "category_id",
            "key",
            unique=True,
            postgresql_where=("category_id IS NOT NULL"),
        ),
        # Partial unique index for global attributes
        Index(
            "ix_category_attributes_global_key",
            "tenant_id",
            "key",
            unique=True,
            postgresql_where=("is_global = true"),
        ),
    )

    # Relationships
    tenant = relationship("Tenant", backref="category_attributes")
    category = relationship("Category", backref="attributes")
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_category_attributes"
    )
    updater = relationship(
        "User", foreign_keys=[updated_by], backref="updated_category_attributes"
    )

    def __repr__(self) -> str:
        return f"<CategoryAttribute {self.name} ({self.key}) for category {self.category_id}>"
