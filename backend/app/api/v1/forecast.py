"""
Forecast API endpoints: compute forecasts for items and return reorder suggestions.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_tenant
from app.core.tenant import TenantContext
from app.models.user import User
from app.models.demand_forecast import DemandForecast
from app.models.inventory import InventoryItem
from app.schemas.response import APIResponse
from app.schemas.forecast import (
    DailyForecast,
    DemandForecastResponse,
    ReorderSuggestion,
)
from app.services.forecast_service import (
    compute_moving_average_forecast,
    compute_exponential_smoothing_forecast,
    generate_reorder_suggestions,
)

router = APIRouter(prefix="/forecast", dependencies=[Depends(get_current_user)])


@router.post("/items/{item_id}", response_model=APIResponse[List[DailyForecast]])
def recompute_item_forecasts(
    item_id: UUID,
    method: str = Query("moving_average", pattern="^(moving_average|exp_smoothing)$"),
    window_size: int = Query(7, ge=1, le=90),
    periods: int = Query(14, ge=1, le=365),
    alpha: float = Query(0.3, gt=0.0, le=1.0),
    user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(require_tenant),
    db: Session = Depends(get_db),
):
    # Validate item belongs to tenant
    item = (
        db.query(InventoryItem)
        .filter(InventoryItem.id == str(item_id))
        .filter(InventoryItem.tenant_id == str(tenant.id))
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if method == "moving_average":
        preds = compute_moving_average_forecast(
            db=db,
            tenant_id=tenant.id,
            item_id=item_id,
            window_size=window_size,
            periods=periods,
        )
        models = [DailyForecast(forecastDate=d, quantity=q, method="moving_average") for d, q in preds]
        return APIResponse(data=models)
    else:
        preds = compute_exponential_smoothing_forecast(
            db=db,
            tenant_id=tenant.id,
            item_id=item_id,
            window_size=window_size,
            periods=periods,
            alpha=alpha,
        )
        models = [DailyForecast(forecastDate=d, quantity=q, method="exp_smoothing") for d, q in preds]
        return APIResponse(data=models)


@router.get("/items/{item_id}", response_model=APIResponse[List[DemandForecastResponse]])
def get_item_forecasts(
    item_id: UUID,
    user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(require_tenant),
    db: Session = Depends(get_db),
):
    forecasts: List[DemandForecast] = (
        db.query(DemandForecast)
        .filter(DemandForecast.tenant_id == str(tenant.id))
        .filter(DemandForecast.item_id == str(item_id))
        .order_by(DemandForecast.forecast_date.asc())
        .all()
    )
    models = [
        DemandForecastResponse(
            id=str(df.id),
            tenantId=str(df.tenant_id),
            itemId=str(df.item_id),
            forecastDate=df.forecast_date,
            quantity=df.quantity,
            method=df.method,
            confidenceLow=df.confidence_low,
            confidenceHigh=df.confidence_high,
            createdAt=df.created_at.isoformat() if df.created_at else date.today().isoformat(),
        )
        for df in forecasts
    ]
    return APIResponse(data=models)


@router.get("/reorder-suggestions", response_model=APIResponse[List[ReorderSuggestion]])
def get_reorder_suggestions(
    category_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    supplier_id: Optional[UUID] = Query(None),  # Optional: reserved for future use
    lead_time_days: int = Query(7, ge=1, le=90),
    user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(require_tenant),
    db: Session = Depends(get_db),
):
    # Base suggestions for all items
    suggestions = generate_reorder_suggestions(db=db, tenant_id=tenant.id, lead_time_days=lead_time_days)

    # Optional filtering by category or location
    if category_id:
        suggestions = [s for s in suggestions if (
            db.query(InventoryItem)
            .filter(InventoryItem.id == s["itemId"])  # s["itemId"] is str
            .filter(InventoryItem.tenant_id == str(tenant.id))
            .filter(InventoryItem.category_id == str(category_id))
            .first()
        )]

    if location_id:
        suggestions = [s for s in suggestions if (
            db.query(InventoryItem)
            .filter(InventoryItem.id == s["itemId"])  # s["itemId"] is str
            .filter(InventoryItem.tenant_id == str(tenant.id))
            .filter(InventoryItem.location_id == str(location_id))
            .first()
        )]

    # supplier_id is not directly tied to inventory items in current schema; ignored for now.

    models = [
        ReorderSuggestion(
            itemId=s["itemId"],
            sku=s["sku"],
            name=s["name"],
            currentStock=s["currentStock"],
            reorderPoint=s["reorderPoint"],
            expectedDemand=s["expectedDemand"],
            leadTimeDays=s["leadTimeDays"],
            recommendedOrderQuantity=s["recommendedOrderQuantity"],
            recommendedOrderDate=s["recommendedOrderDate"],
            rationale=s["rationale"],
        )
        for s in suggestions
    ]
    return APIResponse(data=models)
