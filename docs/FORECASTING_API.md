# Forecasting & Reorder Suggestions API

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
- `sku: string`
- `name: string`
- `currentStock: number`
- `reorderPoint: number`
- `expectedDemand: number` (sum of forecast across lead time)
- `leadTimeDays: number`
- `recommendedOrderQuantity: number`
- `recommendedOrderDate: string | null` (ISO date)
- `rationale: string` (e.g., "Stock at/below reorder point" or "Stock below expected demand over lead time")

Example:

```bash
curl -H "X-Tenant-Slug: demo" \
  "http://localhost:8000/api/v1/forecast/reorder-suggestions?lead_time_days=7"
```

### POST `/api/v1/forecast/items/{item_id}` (method: `moving_average`)

Computes and stores a simple moving average forecast for an item and returns daily predictions. Uses the last N days of consumption (SHIP stock movements) to predict the next `periods` days.

Body: none (parameters via query)

Query params:

- `window_size` (optional, default: `7`): Number of recent days to average.
- `periods` (optional, default: `14`): Number of future days to predict.

Response: `APIResponse<DailyForecast[]>`

`DailyForecast` fields (camelCase):

- `forecastDate: string` (ISO date)
- `quantity: number`
- `method: string` ("moving_average")

Example:

```bash
curl -X POST -H "X-Tenant-Slug: demo" \
  "http://localhost:8000/api/v1/forecast/items/ITEM_UUID?method=moving_average&window_size=7&periods=14"
```

### POST `/api/v1/forecast/items/{item_id}` (method: `exp_smoothing`)

Computes and stores a single exponential smoothing forecast for an item and returns daily predictions.

Body: none (parameters via query)

Query params:

- `window_size` (optional, default: `7`)
- `periods` (optional, default: `14`)
- `alpha` (optional, default: `0.3`, range `(0, 1]`): Smoothing factor.

Response: `APIResponse<DailyForecast[]>`

`DailyForecast` fields (camelCase):

- `forecastDate: string` (ISO date)
- `quantity: number`
- `method: string` ("exp_smoothing")

Example:

```bash
curl -X POST -H "X-Tenant-Slug: demo" \
  "http://localhost:8000/api/v1/forecast/items/ITEM_UUID?method=exp_smoothing&window_size=7&periods=14&alpha=0.3"
```

## How Forecasts Are Computed

- **Consumption source:** Outbound `StockMovement` records (`movement_type = ship`). Quantities are treated as positive consumption (i.e., `-(quantity)` when quantity is negative).
- **Moving Average:** Average of the last `window_size` daily consumptions; this per-day value is projected uniformly across the next `periods` days.
- **Exponential Smoothing:** Single ES over the last `window_size` daily consumptions with smoothing factor `alpha`; the final smoothed level is projected uniformly for the next `periods` days.
- **Storage:** Predictions are upserted into `demand_forecasts` with method labels (`moving_average`, `exp_smoothing`) and simple confidence bounds (±20%).

## Reorder Suggestions Logic

- **Expected Demand:** Sum of forecasted quantities for the next `lead_time_days` days. If no forecasts exist, the system calculates moving average forecasts on the fly.
- **Current Stock:** Uses `InventoryItem.total_quantity` (sum of lots if present, otherwise the `quantity` field).
- **Reorder Trigger:** Occurs when `currentStock <= reorderPoint` OR `currentStock <= expectedDemand`.
- **Recommended Quantity:** `max(expectedDemand + reorderPoint - currentStock, 0)`.
- **Recommended Date:** Today if a reorder is recommended; otherwise `null`.

## Notes & Best Practices

- Ensure regular inbound/outbound movements are recorded to improve forecast accuracy.
- For more advanced planning (safety stock, EOQ, detailed lead time per supplier), the service can be extended or integrated with analytics engines.
- All endpoints respect tenant RLS (Row Level Security); data is filtered by `tenant_id` automatically.
