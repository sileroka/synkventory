"""
Sales order counter model to generate tenant-scoped sequential order numbers.
"""

import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class SalesOrderCounter(Base):
    """Stores per-tenant per-day counters for sales order numbers."""

    __tablename__ = "sales_order_counters"
    __table_args__ = (
        UniqueConstraint("tenant_id", "date_key", name="uq_so_counter_tenant_date"),
    )

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

    # Use a string date key (YYYYMMDD) to keep numbering consistent with prefixes
    date_key = Column(String(8), nullable=False, index=True)

    # Last sequence issued for this tenant/date
    last_seq = Column(Integer, nullable=False, default=0)

    # Audit
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    tenant = relationship("Tenant", backref="sales_order_counters")

    def __repr__(self) -> str:
        return f"<SalesOrderCounter tenant={self.tenant_id} date={self.date_key} last_seq={self.last_seq}>"
