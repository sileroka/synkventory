# Forecasting & Reorder Suggestions API

## Deprecation Notice

- The legacy `/api/v1/forecasting/*` endpoints are deprecated and replaced by `/api/v1/forecast/*`.
- Client applications should migrate to `/forecast/*`. The UI now routes to `/forecast` and `/forecast/reorder-suggestions`, with a client-side redirect from the old path.

Synkventory adds basic demand forecasting and reorder suggestions to help optimize inventory levels and reduce stock-outs.

This document describes the available endpoints, request parameters, response shapes, and multi-tenancy/auth considerations.

## Auth & Tenancy

- All endpoints require authentication and a valid tenant context.
- In development/testing, send the `X-Tenant-Slug` header (e.g., `demo` or `test-tenant`).
- Cookies-based auth is used; in tests/examples below, assume you already have a valid session or use `-b cookies.txt`.

## Endpoints

### GET `/api/v1/forecast/reorder-suggestions`

Returns reorder suggestions for all items in the current tenant based on forecasted demand, current stock (including lots), lead time, and reorder point.

Query params:

- `lead_time_days` (optional, default: `7`): Number of days of lead time to consider.

Response: `APIResponse<ReorderSuggestion[]>`

`ReorderSuggestion` fields (camelCase):

- `itemId: string`
- `itemName: string`
- `currentQuantity: number`
- `forecastedNeed: number`
- `suggestedOrderQuantity: number`
- `suggestedOrderDate: string | null` (ISO date)

Example:

```bash
curl -H "X-Tenant-Slug: demo" \
  "http://localhost:8000/api/v1/forecast/reorder-suggestions?lead_time_days=7"
```

### POST `/api/v1/forecast/items/{item_id}`

Computes and stores a forecast for an item and returns daily predictions. Uses the last N days of consumption (SHIP stock movements).

Body: `ForecastRequest` (JSON)

```json
{
  "method": "moving_average", // or "exp_smoothing"
  "windowSize": 7,
  "periods": 14,
  "alpha": 0.3 // optional, for exp_smoothing only
}
```

Response: `APIResponse<DailyForecast[]>`

`DailyForecast` fields (camelCase):

- `forecastDate: string` (ISO date)
- `quantity: number`
- `method: string` ("moving_average" or "exp_smoothing")

Examples:

```bash
curl -X POST -H "Content-Type: application/json" -H "X-Tenant-Slug: demo" \
  -d '{"method":"moving_average","windowSize":7,"periods":14}' \
  "http://localhost:8000/api/v1/forecast/items/ITEM_UUID"

curl -X POST -H "Content-Type: application/json" -H "X-Tenant-Slug: demo" \
  -d '{"method":"exp_smoothing","windowSize":7,"periods":14,"alpha":0.3}' \
  "http://localhost:8000/api/v1/forecast/items/ITEM_UUID"
```

## How Forecasts Are Computed

- **Consumption source:** Outbound `StockMovement` records (`movement_type = ship`). Quantities are treated as positive consumption (i.e., `-(quantity)` when quantity is negative).
- **Moving Average:** Average of the last `window_size` daily consumptions; this per-day value is projected uniformly across the next `periods` days.
- **Exponential Smoothing:** Single ES over the last `window_size` daily consumptions with smoothing factor `alpha`; the final smoothed level is projected uniformly for the next `periods` days.
- **Storage:** Predictions are upserted into `demand_forecasts` with method labels (`moving_average`, `exp_smoothing`) and simple confidence bounds (±20%).

## Reorder Suggestions Logic

- **Expected Demand:** Sum of forecasted quantities for the next `lead_time_days` days. If no forecasts exist, the system calculates moving average forecasts on the fly.
- **Current Stock:** Uses `InventoryItem.total_quantity` (sum of lots if present, otherwise the `quantity` field).
- **Reorder Trigger:** Occurs when `currentQuantity <= forecastedNeed` (or below internal reorder point if still tracked).
- **Recommended Quantity:** `max(forecastedNeed + reorderPoint - currentStock, 0)`.
- **Recommended Date:** Today if a reorder is recommended; otherwise `null`.

## Notes & Best Practices

- Ensure regular inbound/outbound movements are recorded to improve forecast accuracy.
- For more advanced planning (safety stock, EOQ, detailed lead time per supplier), the service can be extended or integrated with analytics engines.
- All endpoints respect tenant RLS (Row Level Security); data is filtered by `tenant_id` automatically.
