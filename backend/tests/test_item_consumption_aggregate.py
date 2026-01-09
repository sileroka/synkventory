import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.item_consumption import ItemConsumption
from app.schemas.stock_movement import StockMovementCreate, MovementType
from app.services.stock_movement_service import stock_movement_service
from app.models.inventory import InventoryItem


def test_multiple_shipments_aggregate_to_single_record(db: Session, system_user):
    from app.models.location import Location
    from app.models.inventory_location_quantity import InventoryLocationQuantity

    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(system_user.tenant_id),
        name="Widget Agg",
        sku="WIDGET-AGG",
        quantity=20,
        reorder_point=1,
        status="in_stock",
    )
    loc = Location(tenant_id=system_user.tenant_id, name="Main", code="MAIN")
    db.add_all([item, loc])
    db.commit()
    db.refresh(item)
    db.refresh(loc)

    # Seed per-location qty
    db.add(InventoryLocationQuantity(inventory_item_id=str(item.id), location_id=str(loc.id), quantity=20))
    db.commit()

    # Two shipments on same day
    m1 = StockMovementCreate(
        inventory_item_id=str(item.id), movement_type=MovementType.SHIP, quantity=-5, from_location_id=str(loc.id)
    )
    m2 = StockMovementCreate(
        inventory_item_id=str(item.id), movement_type=MovementType.SHIP, quantity=-3, from_location_id=str(loc.id)
    )
    stock_movement_service.create_movement(db=db, movement=m1, user_id=system_user.id)
    stock_movement_service.create_movement(db=db, movement=m2, user_id=system_user.id)

    # Assert single consumption record with summed qty
    today = datetime.utcnow().date()
    rows = db.query(ItemConsumption).filter(ItemConsumption.item_id == str(item.id), ItemConsumption.date == today).all()
    assert len(rows) == 1
    assert rows[0].quantity == Decimal("8")
