"""
Pydantic schemas for forecasting endpoints.
"""

from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional
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
    item_name: str = Field(..., alias="itemName")
    current_quantity: int = Field(..., alias="currentQuantity")
    forecasted_need: int = Field(..., alias="forecastedNeed")
    suggested_order_quantity: int = Field(..., alias="suggestedOrderQuantity")
    suggested_order_date: Optional[date] = Field(None, alias="suggestedOrderDate")


class DemandForecastResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    forecast_date: date = Field(..., alias="forecastDate")
    quantity: int
    method: str


class ForecastRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    method: Literal["moving_average", "exp_smoothing"] = Field("moving_average")
    window_size: int = Field(7, ge=1, le=90)
    periods: int = Field(14, ge=1, le=365)
    alpha: float | None = Field(0.3, gt=0.0, le=1.0)
