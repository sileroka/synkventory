import uuid
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Index, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

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
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    forecast_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    method = Column(String(50), nullable=False)
    confidence_low = Column(Float, nullable=True)
    confidence_high = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "ix_demand_forecasts_tenant_item_date",
            "tenant_id",
            "item_id",
            "forecast_date",
            unique=False,
        ),
    )

    # Relationships
    tenant = relationship("Tenant", backref="demand_forecasts")
    item = relationship("InventoryItem", backref="demand_forecasts")

    def __repr__(self) -> str:
        return f"<DemandForecast item={self.item_id} date={self.forecast_date} qty={self.quantity} method={self.method}>"
