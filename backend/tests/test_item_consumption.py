import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.item_consumption import ItemConsumption, ConsumptionSource
from app.schemas.stock_movement import StockMovementCreate, MovementType
from app.services.stock_movement_service import stock_movement_service
from app.models.inventory import InventoryItem


def test_ship_creates_consumption_record(db: Session, system_user):
    # Arrange: create item and location
    from app.models.location import Location
    from app.models.inventory_location_quantity import InventoryLocationQuantity
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(system_user.tenant_id),
        name="Widget A",
        sku="WIDGET-A",
        quantity=10,
        reorder_point=1,
        status="in_stock",
    )
    loc = Location(tenant_id=system_user.tenant_id, name="Main", code="MAIN")
    db.add_all([item, loc])
    db.commit()
    db.refresh(item)
    db.refresh(loc)

    # Seed per-location quantity
    db.add(
        InventoryLocationQuantity(
            inventory_item_id=str(item.id), location_id=str(loc.id), quantity=10
        )
    )
    db.commit()

    # Act: create a ship movement (-3)
    movement = StockMovementCreate(
        inventory_item_id=str(item.id),
        movement_type=MovementType.SHIP,
        quantity=-3,
        from_location_id=str(loc.id),
        to_location_id=None,
        lot_id=None,
        reference_number="SO-TEST",
        notes="Test shipment",
    )
    stock_movement_service.create_movement(db=db, movement=movement, user_id=system_user.id)

    # Assert: one consumption entry with qty 3 and source SALES_ORDER
    consumption = db.query(ItemConsumption).filter(ItemConsumption.item_id == str(item.id)).all()
    assert len(consumption) == 1
    rec = consumption[0]
    assert rec.quantity == Decimal("3")
    assert rec.source == ConsumptionSource.SALES_ORDER
    assert rec.date == datetime.utcnow().date()


def test_transfer_does_not_create_consumption(db: Session, system_user):
    # Arrange: create item and two locations with stock
    from app.models.location import Location
    from app.models.inventory_location_quantity import InventoryLocationQuantity

    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(system_user.tenant_id),
        name="Widget B",
        sku="WIDGET-B",
        quantity=10,
        reorder_point=1,
        status="in_stock",
    )
    loc_from = Location(tenant_id=system_user.tenant_id, name="A", code="A")
    loc_to = Location(tenant_id=system_user.tenant_id, name="B", code="B")
    db.add_all([item, loc_from, loc_to])
    db.commit()
    db.refresh(item)
    db.refresh(loc_from)
    db.refresh(loc_to)

    # seed location qty
    db.add(InventoryLocationQuantity(inventory_item_id=str(item.id), location_id=str(loc_from.id), quantity=5))
    db.add(InventoryLocationQuantity(inventory_item_id=str(item.id), location_id=str(loc_to.id), quantity=5))
    db.commit()

    # Act: transfer 2 from A to B
    movement = StockMovementCreate(
        inventory_item_id=str(item.id),
        movement_type=MovementType.TRANSFER,
        quantity=2,
        from_location_id=str(loc_from.id),
        to_location_id=str(loc_to.id),
        lot_id=None,
        reference_number="XFER-1",
        notes="Test transfer",
    )
    stock_movement_service.create_movement(db=db, movement=movement, user_id=system_user.id)

    # Assert: no consumption records created
    count = db.query(ItemConsumption).filter(ItemConsumption.item_id == str(item.id)).count()
    assert count == 0
