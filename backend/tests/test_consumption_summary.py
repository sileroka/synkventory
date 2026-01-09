from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.item_consumption import ItemConsumption, ConsumptionSource
from app.models.inventory import InventoryItem
from app.api.v1.reports import router
from app.main import app
from fastapi.testclient import TestClient


def test_consumption_summary_basic(db: Session, system_user):
    # Seed items
    item = InventoryItem(
        id=str(system_user.id).replace("-", "")[:32],
        tenant_id=str(system_user.tenant_id),
        name="Widget C",
        sku="WIDGET-C",
        quantity=0,
        reorder_point=1,
        status="in_stock",
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # Seed consumption records over two days
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    db.add_all([
        ItemConsumption(tenant_id=system_user.tenant_id, item_id=str(item.id), date=yesterday, quantity=2, source=ConsumptionSource.OTHER, created_by=system_user.id),
        ItemConsumption(tenant_id=system_user.tenant_id, item_id=str(item.id), date=yesterday, quantity=3, source=ConsumptionSource.OTHER, created_by=system_user.id),
        ItemConsumption(tenant_id=system_user.tenant_id, item_id=str(item.id), date=today, quantity=5, source=ConsumptionSource.OTHER, created_by=system_user.id),
    ])
    db.commit()

    client = TestClient(app)
    resp = client.get(
        "/api/v1/reports/consumption-summary",
        params={
            "startDate": yesterday.isoformat(),
            "endDate": today.isoformat(),
            "itemIds": [str(item.id)],
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["startDate"]
    assert len(data["entries"]) == 2  # two days aggregated
    totals = {e["date"]: e["totalConsumed"] for e in data["entries"]}
    # Convert dates to date-only strings
    # Verify aggregated totals
    assert any(v == 5.0 for v in totals.values())
    assert any(v == 5.0 for v in totals.values())  # 2 + 3 yesterday
