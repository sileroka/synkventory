"""
Forecasting service for inventory demand planning.

Provides:
- Moving average forecast over recent daily consumption
- Optional exponential smoothing forecast
- Reorder suggestions based on forecasted demand, current stock, lead time, and reorder point

Follows Synkventory multi-tenancy and RLS guidelines: all queries filter by `tenant_id`.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.stock_movement import StockMovement, MovementType
from app.models.inventory import InventoryItem
from app.models.demand_forecast import DemandForecast


DEFAULT_LEAD_TIME_DAYS = 7
DEFAULT_MOVING_AVG_WINDOW = 7
DEFAULT_ES_ALPHA = 0.3


def _normalize_uuid(value: UUID | str) -> str:
    """Return a safe string form of a UUID for cross-dialect filters."""
    return str(value)


def _daily_consumption_series(
    db: Session,
    tenant_id: UUID,
    item_id: UUID,
    window_days: int,
    until: Optional[date] = None,
) -> List[int]:
    """
    Build a list of daily consumption quantities for the last `window_days` days.
    Consumption is derived from outbound stock movements (SHIP). Quantities are
    considered positive for consumption (i.e., -movement.quantity when movement.quantity is negative).
    Days with no movement count as 0.
    """
    end_date = until or date.today()
    start_date = end_date - timedelta(days=window_days)

    movements = (
        db.query(StockMovement)
        .filter(StockMovement.tenant_id == _normalize_uuid(tenant_id))
        .filter(StockMovement.inventory_item_id == _normalize_uuid(item_id))
        .filter(StockMovement.movement_type == MovementType.SHIP)
        .filter(StockMovement.created_at >= datetime.combine(start_date, datetime.min.time()))
        .filter(StockMovement.created_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()))
        .all()
    )

    by_day: Dict[date, int] = {}
    for m in movements:
        d = (m.created_at.date() if isinstance(m.created_at, datetime) else m.created_at)
        qty_out = -(m.quantity) if m.quantity < 0 else 0
        by_day[d] = by_day.get(d, 0) + qty_out

    series: List[int] = []
    for i in range(window_days):
        d = start_date + timedelta(days=i)
        series.append(by_day.get(d, 0))
    return series


def compute_moving_average_forecast(
    db: Session,
    tenant_id: UUID,
    item_id: UUID,
    window_size: int,
    periods: int,
) -> List[Tuple[date, int]]:
    """
    Calculate a simple moving average forecast based on the last `window_size` days
    of consumption. Returns a list of (forecast_date, quantity) for the next `periods` days
    and inserts/updates DemandForecast records with method="moving_average".
    """
    if window_size <= 0:
        window_size = DEFAULT_MOVING_AVG_WINDOW
    if periods <= 0:
        return []

    series = _daily_consumption_series(db, tenant_id, item_id, window_size)
    avg = sum(series) / float(window_size) if window_size > 0 else 0.0
    predicted_per_day = max(int(round(avg)), 0)

    results: List[Tuple[date, int]] = []
    today = date.today()
    for i in range(1, periods + 1):
        f_date = today + timedelta(days=i)
        results.append((f_date, predicted_per_day))

        # Upsert forecast record
        existing = (
            db.query(DemandForecast)
            .filter(DemandForecast.tenant_id == _normalize_uuid(tenant_id))
            .filter(DemandForecast.item_id == _normalize_uuid(item_id))
            .filter(DemandForecast.forecast_date == f_date)
            .first()
        )
        if existing:
            existing.quantity = predicted_per_day
            existing.method = "moving_average"
            existing.confidence_low = max(predicted_per_day * 0.8, 0)
            existing.confidence_high = predicted_per_day * 1.2
        else:
            df = DemandForecast(
                id=str(uuid.uuid4()),
                tenant_id=_normalize_uuid(tenant_id),
                item_id=_normalize_uuid(item_id),
                forecast_date=f_date,
                quantity=predicted_per_day,
                method="moving_average",
                confidence_low=max(predicted_per_day * 0.8, 0),
                confidence_high=predicted_per_day * 1.2,
            )
            db.add(df)
    db.commit()

    return results


def compute_exponential_smoothing_forecast(
    db: Session,
    tenant_id: UUID,
    item_id: UUID,
    window_size: int,
    periods: int,
    alpha: float = DEFAULT_ES_ALPHA,
) -> List[Tuple[date, int]]:
    """
    Compute a single exponential smoothing forecast over the last `window_size` days
    with smoothing factor `alpha`. Forecast for each of the next `periods` days is the
    final smoothed level. Inserts/updates DemandForecast with method="exp_smoothing".
    """
    if window_size <= 0:
        window_size = DEFAULT_MOVING_AVG_WINDOW
    if periods <= 0:
        return []
    if not (0.0 < alpha <= 1.0):
        alpha = DEFAULT_ES_ALPHA

    series = _daily_consumption_series(db, tenant_id, item_id, window_size)
    if not series:
        smoothed = 0.0
    else:
        smoothed = float(series[0])
        for x in series[1:]:
            smoothed = alpha * float(x) + (1.0 - alpha) * smoothed

    predicted_per_day = max(int(round(smoothed)), 0)

    results: List[Tuple[date, int]] = []
    today = date.today()
    for i in range(1, periods + 1):
        f_date = today + timedelta(days=i)
        results.append((f_date, predicted_per_day))

        existing = (
            db.query(DemandForecast)
            .filter(DemandForecast.tenant_id == _normalize_uuid(tenant_id))
            .filter(DemandForecast.item_id == _normalize_uuid(item_id))
            .filter(DemandForecast.forecast_date == f_date)
            .first()
        )
        if existing:
            existing.quantity = predicted_per_day
            existing.method = "exp_smoothing"
            existing.confidence_low = max(predicted_per_day * 0.8, 0)
            existing.confidence_high = predicted_per_day * 1.2
        else:
            df = DemandForecast(
                id=str(uuid.uuid4()),
                tenant_id=_normalize_uuid(tenant_id),
                item_id=_normalize_uuid(item_id),
                forecast_date=f_date,
                quantity=predicted_per_day,
                method="exp_smoothing",
                confidence_low=max(predicted_per_day * 0.8, 0),
                confidence_high=predicted_per_day * 1.2,
            )
            db.add(df)
    db.commit()

    return results


def generate_reorder_suggestions(
    db: Session,
    tenant_id: UUID,
    lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
) -> List[dict]:
    """
    Generate reorder suggestions for all items in a tenant.

    Logic:
    - Expected demand over lead time = sum of DemandForecast for next `lead_time_days` days.
      If no forecasts exist, fallback to moving average (window=DEFAULT_MOVING_AVG_WINDOW, periods=lead_time_days).
    - Current stock = `InventoryItem.total_quantity` (lots sum or quantity).
    - Reorder when: current_stock <= reorder_point OR current_stock <= expected_demand.
    - Recommended qty = max(0, expected_demand + reorder_point - current_stock).
    - Recommended date = today if recommended qty > 0, else None.
    """
    today = date.today()
    normalize_tid = _normalize_uuid(tenant_id)

    items: List[InventoryItem] = (
        db.query(InventoryItem)
        .filter(InventoryItem.tenant_id == normalize_tid)
        .all()
    )

    suggestions: List[dict] = []
    for item in items:
        # Sum existing forecasts over lead time
        forecasts = (
            db.query(DemandForecast)
            .filter(DemandForecast.tenant_id == normalize_tid)
            .filter(DemandForecast.item_id == _normalize_uuid(item.id))
            .filter(DemandForecast.forecast_date >= today + timedelta(days=1))
            .filter(DemandForecast.forecast_date <= today + timedelta(days=lead_time_days))
            .all()
        )
        expected_demand = sum(df.quantity or 0 for df in forecasts)

        # Fallback: compute moving average forecasts if none present
        if expected_demand == 0:
            preds = compute_moving_average_forecast(
                db,
                tenant_id=tenant_id,
                item_id=item.id,
                window_size=DEFAULT_MOVING_AVG_WINDOW,
                periods=lead_time_days,
            )
            expected_demand = sum(qty for _, qty in preds)

        current_stock = item.total_quantity
        reorder_point = item.reorder_point or 0

        needs_reorder = (current_stock <= reorder_point) or (current_stock <= expected_demand)
        recommended_qty = max(expected_demand + reorder_point - current_stock, 0)
        recommended_date = today if recommended_qty > 0 and needs_reorder else None

        suggestions.append(
            {
                "itemId": str(item.id),
                "sku": item.sku,
                "name": item.name,
                "currentStock": int(current_stock or 0),
                "reorderPoint": int(reorder_point or 0),
                "expectedDemand": int(expected_demand or 0),
                "leadTimeDays": int(lead_time_days),
                "recommendedOrderQuantity": int(recommended_qty),
                "recommendedOrderDate": recommended_date,
                "rationale": (
                    "Stock at/below reorder point" if current_stock <= reorder_point else (
                        "Stock below expected demand over lead time" if current_stock <= expected_demand else "Sufficient stock"
                    )
                ),
            }
        )

    return suggestions
