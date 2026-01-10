"""
Pydantic schemas for forecasting endpoints.
"""

from __future__ import annotations

from datetime import date
from typing import List
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.response import to_camel


class DailyForecast(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    forecast_date: date = Field(..., alias="forecastDate")
    quantity: int
    method: str


class ReorderSuggestion(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    item_id: str = Field(..., alias="itemId")
    sku: str
    name: str
    current_stock: int = Field(..., alias="currentStock")
    reorder_point: int = Field(..., alias="reorderPoint")
    expected_demand: int = Field(..., alias="expectedDemand")
    lead_time_days: int = Field(..., alias="leadTimeDays")
    recommended_order_quantity: int = Field(..., alias="recommendedOrderQuantity")
    recommended_order_date: date | None = Field(None, alias="recommendedOrderDate")
    rationale: str


class DemandForecastResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    tenant_id: str = Field(..., alias="tenantId")
    item_id: str = Field(..., alias="itemId")
    forecast_date: date = Field(..., alias="forecastDate")
    quantity: int
    method: str
    confidence_low: float | None = Field(None, alias="confidenceLow")
    confidence_high: float | None = Field(None, alias="confidenceHigh")
    created_at: str = Field(..., alias="createdAt")
