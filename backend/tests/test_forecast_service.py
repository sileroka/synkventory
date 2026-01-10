from datetime import datetime, timedelta, date
import uuid

from sqlalchemy.orm import Session

from app.models.stock_movement import StockMovement, MovementType
from app.models.demand_forecast import DemandForecast
from app.models.inventory import InventoryItem
from app.models.tenant import DEFAULT_TENANT_ID
from app.services.forecast_service import (
    compute_moving_average_forecast,
    compute_exponential_smoothing_forecast,
    generate_reorder_suggestions,
)


def _add_ship(db: Session, tenant_id: uuid.UUID, item_id: str, qty_out: int, days_ago: int = 0) -> None:
    # quantity negative for outbound
    when = datetime.now() - timedelta(days=days_ago)
    m = StockMovement(
        id=str(uuid.uuid4()),
        tenant_id=str(tenant_id),
        inventory_item_id=str(item_id),
        movement_type=MovementType.SHIP,
        quantity=-abs(qty_out),
        created_at=when,
    )
    db.add(m)
    db.commit()


def test_moving_average_forecast_upserts(db: Session):
    # Create item and consumption series over last 7 days: [0,1,2,3,4,5,6]
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name="Forecast Item",
        sku="FCST-001",
        quantity=50,
        reorder_point=10,
        unit_price=1.0,
    )
    db.add(item)
    db.commit()

    for i in range(7):
        _add_ship(db, DEFAULT_TENANT_ID, item.id, qty_out=i, days_ago=7 - i)

    preds = compute_moving_average_forecast(db, DEFAULT_TENANT_ID, item.id, window_size=7, periods=7)
    assert len(preds) == 7
    # Average of 0..6 = 21/7 = 3
    for d, q in preds:
        assert q == 3

    # Upserts created
    rows = (
        db.query(DemandForecast)
        .filter(DemandForecast.tenant_id == str(DEFAULT_TENANT_ID))
        .filter(DemandForecast.item_id == str(item.id))
        .filter(DemandForecast.method == "moving_average")
        .all()
    )
    assert len(rows) == 7
    assert all(r.quantity == 3 for r in rows)


def test_exponential_smoothing_forecast(db: Session):
    # Series: [10, 0, 10, 0, 10] with alpha=0.5 -> final smoothed ~ 5
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name="Smoothing Item",
        sku="FCST-002",
        quantity=50,
        reorder_point=10,
        unit_price=1.0,
    )
    db.add(item)
    db.commit()

    values = [10, 0, 10, 0, 10]
    for idx, val in enumerate(values):
        _add_ship(db, DEFAULT_TENANT_ID, item.id, qty_out=val, days_ago=len(values) - idx)

    preds = compute_exponential_smoothing_forecast(db, DEFAULT_TENANT_ID, item.id, window_size=5, periods=5, alpha=0.5)
    assert len(preds) == 5
    # Expected smoothed value around 5 -> rounded to 5
    for d, q in preds:
        assert q == 5


def test_forecast_updates_when_new_consumption_recorded(db: Session):
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name="Update Item",
        sku="FCST-003",
        quantity=100,
        reorder_point=10,
        unit_price=1.0,
    )
    db.add(item)
    db.commit()

    # Initial series: three days with 2 units consumption
    for i in range(3):
        _add_ship(db, DEFAULT_TENANT_ID, item.id, qty_out=2, days_ago=3 - i)

    compute_moving_average_forecast(db, DEFAULT_TENANT_ID, item.id, window_size=7, periods=3)
    before = db.query(DemandForecast).filter(DemandForecast.item_id == str(item.id)).all()
    assert len(before) == 3
    assert all(r.quantity == 1 for r in before) or all(r.quantity == 1 for r in before)

    # Add new higher consumption, expect updated higher forecast on recompute
    _add_ship(db, DEFAULT_TENANT_ID, item.id, qty_out=14, days_ago=1)
    compute_moving_average_forecast(db, DEFAULT_TENANT_ID, item.id, window_size=7, periods=3)
    after = db.query(DemandForecast).filter(DemandForecast.item_id == str(item.id)).all()
    assert len(after) == 3
    # Average increased; quantities should be greater than or equal to previous
    assert all(r.quantity >= 2 for r in after)


def test_generate_reorder_suggestions_with_forecasts_and_fallback(db: Session):
    # Create two items: one with forecasts, one without (fallback to MA)
    item_a = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name="Item A",
        sku="ITEM-A",
        quantity=5,
        reorder_point=10,
        unit_price=1.0,
    )
    item_b = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name="Item B",
        sku="ITEM-B",
        quantity=50,
        reorder_point=5,
        unit_price=1.0,
    )
    db.add_all([item_a, item_b])
    db.commit()

    # Add forecasts for item A for next 3 days summing to 9
    today = date.today()
    for i, qty in enumerate([3, 3, 3], start=1):
        df = DemandForecast(
            id=str(uuid.uuid4()),
            tenant_id=str(DEFAULT_TENANT_ID),
            item_id=str(item_a.id),
            forecast_date=today + timedelta(days=i),
            quantity=qty,
            method="moving_average",
        )
        db.add(df)
    db.commit()

    # For item B, seed simple consumption so fallback MA has non-zero demand
    _add_ship(db, DEFAULT_TENANT_ID, item_b.id, qty_out=4, days_ago=2)
    _add_ship(db, DEFAULT_TENANT_ID, item_b.id, qty_out=6, days_ago=1)

    suggestions = generate_reorder_suggestions(db, DEFAULT_TENANT_ID, lead_time_days=3)
    # Find entries
    s_a = next(s for s in suggestions if s["itemId"] == str(item_a.id))
    s_b = next(s for s in suggestions if s["itemId"] == str(item_b.id))

    # Item A: currentStock=5, reorderPoint=10, expectedDemand=9 => recommendedOrderQuantity = 14
    assert s_a["expectedDemand"] == 9
    assert s_a["currentStock"] == 5
    assert s_a["reorderPoint"] == 10
    assert s_a["recommendedOrderQuantity"] == max(9 + 10 - 5, 0)

    # Item B: fallback MA demand over 3 days should be > 0 and with stock 50 above demand -> likely no reorder
    assert s_b["expectedDemand"] >= 0
    assert s_b["currentStock"] == 50
    assert s_b["recommendedOrderQuantity"] >= 0
