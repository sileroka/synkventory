---
applyTo: "**"
---

Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

# Synkventory Development Standards

## Brand Identity

- **Product Name:** Synkventory
- **Tagline:** Stock in sync.
- **Parent Company:** Synkadia

---

## Color Palette

### Primary Colors

| Role      | Name       | Hex       | RGB           | Usage                                                          |
| --------- | ---------- | --------- | ------------- | -------------------------------------------------------------- |
| Primary   | Deep Teal  | `#0D9488` | 13, 148, 136  | Brand color, navigation, headers, primary buttons              |
| Secondary | Coral      | `#F87171` | 248, 113, 113 | Secondary actions, accents, interactive elements, hover states |
| Tertiary  | Slate Blue | `#6366F1` | 99, 102, 241  | Links, data visualizations, informational highlights           |

### Neutral Colors

| Role        | Name        | Hex       | Usage                             |
| ----------- | ----------- | --------- | --------------------------------- |
| Neutral 900 | Slate Dark  | `#0F172A` | Primary text, headings            |
| Neutral 700 | Slate 700   | `#334155` | Secondary text                    |
| Neutral 500 | Slate Mid   | `#64748B` | Muted text, placeholders          |
| Neutral 300 | Slate 300   | `#CBD5E1` | Borders, dividers                 |
| Neutral 100 | Slate Light | `#F1F5F9` | Backgrounds, cards                |
| White       | White       | `#FFFFFF` | Page background, card backgrounds |

### Semantic Colors

| State   | Hex       | Usage                                                 |
| ------- | --------- | ----------------------------------------------------- |
| Success | `#10B981` | Confirmations, in-stock indicators, completed actions |
| Warning | `#F59E0B` | Caution states, expiring items, reorder points        |
| Error   | `#EF4444` | Errors, validation failures, critical stock levels    |
| Info    | `#6366F1` | Informational messages (uses Tertiary)                |

---

## Typography

### Font Stack

```css
--font-primary: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-mono: "JetBrains Mono", "Fira Code", "Consolas", monospace;
```

### Scale

| Element | Size            | Weight | Line Height |
| ------- | --------------- | ------ | ----------- |
| H1      | 2rem (32px)     | 700    | 1.2         |
| H2      | 1.5rem (24px)   | 600    | 1.3         |
| H3      | 1.25rem (20px)  | 600    | 1.4         |
| H4      | 1rem (16px)     | 600    | 1.4         |
| Body    | 0.875rem (14px) | 400    | 1.5         |
| Small   | 0.75rem (12px)  | 400    | 1.5         |
| Caption | 0.625rem (10px) | 500    | 1.4         |

---

## UI Components (PrimeNG)

### Button Hierarchy

1. **Primary:** Deep Teal (`#0D9488`) — Main actions (Save, Submit, Create)
2. **Secondary:** Coral (`#F87171`) — Secondary actions (Edit, View Details)
3. **Tertiary:** Slate Blue (`#6366F1`) — Tertiary actions, links
4. **Outlined:** Teal border, transparent fill — Minimal emphasis actions
5. **Danger:** Error Red (`#EF4444`) — Destructive actions (Delete, Remove)
6. **Text:** No background — Minimal actions (Cancel, Close)

### Component Styling

```scss
// PrimeNG theme overrides
$primaryColor: #0d9488;
$primaryDarkColor: #0f766e;
$primaryLightColor: #14b8a6;

$secondaryColor: #f87171;
$tertiaryColor: #6366f1;
$dangerColor: #ef4444;
$successColor: #10b981;
$warningColor: #f59e0b;

// Border radius
$borderRadius: 0.5rem;

// Shadows
$shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
$shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
$shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
```

### Data Tables

- Use alternating row colors: White / Slate 100 (`#F1F5F9`)
- Highlight on hover: Teal at 10% opacity
- Selected row: Teal at 15% opacity with left border accent
- Low stock rows: Coral left border indicator
- Sortable columns: Tertiary Slate Blue icons

### Status Badges

| Status       | Background | Text      |
| ------------ | ---------- | --------- |
| In Stock     | `#D1FAE5`  | `#065F46` |
| Low Stock    | `#FEF3C7`  | `#92400E` |
| Out of Stock | `#FEE2E2`  | `#991B1B` |
| On Order     | `#E0E7FF`  | `#3730A3` |
| Discontinued | `#E2E8F0`  | `#475569` |

---

## Coding Standards

### Angular/TypeScript

```typescript
// Use standalone components
@Component({
  standalone: true,
  selector: 'app-inventory-list',
  imports: [CommonModule, TableModule, ButtonModule],
  templateUrl: './inventory-list.component.html'
})

// Naming conventions
// Components: PascalCase with Component suffix
// Services: PascalCase with Service suffix
// Interfaces: PascalCase, prefix with I for data models
// Constants: SCREAMING_SNAKE_CASE
// Variables/functions: camelCase

// Example interface
export interface IInventoryItem {
  id: string;
  sku: string;
  name: string;
  quantity: number;
  reorderPoint: number;
  status: InventoryStatus;
  lastUpdated: Date;
}

// Use enums for fixed values
export enum InventoryStatus {
  IN_STOCK = 'in_stock',
  LOW_STOCK = 'low_stock',
  OUT_OF_STOCK = 'out_of_stock',
  ON_ORDER = 'on_order',
  DISCONTINUED = 'discontinued'
}

// Prefer signals for state management (Angular 17+)
export class InventoryComponent {
  items = signal<IInventoryItem[]>([]);
  selectedItem = signal<IInventoryItem | null>(null);
  isLoading = signal(false);
}
```

### Python/FastAPI

```python
# Use type hints everywhere
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# Pydantic models for API
class InventoryItemBase(BaseModel):
    sku: str
    name: str
    quantity: int
    reorder_point: int

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: str
    status: str
    last_updated: datetime

    class Config:
        from_attributes = True

# Router naming: plural nouns
# /api/v1/inventory-items
# /api/v1/locations
# /api/v1/stock-movements

# Use dependency injection for services
async def get_inventory_service(
    db: AsyncSession = Depends(get_db)
) -> InventoryService:
    return InventoryService(db)

# Snake_case for Python, but camelCase in JSON responses
# Use Pydantic's alias_generator for automatic conversion
```

### Database (PostgreSQL)

```sql
-- Table naming: plural, snake_case
-- inventory_items, stock_movements, locations

-- Always include audit columns
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'in_stock',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Index naming: idx_{table}_{column(s)}
CREATE INDEX idx_inventory_items_sku ON inventory_items(sku);
CREATE INDEX idx_inventory_items_status ON inventory_items(status);
```

---

## File Structure

```
synkventory/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/           # Singleton services, guards, interceptors
│   │   │   ├── shared/         # Shared components, pipes, directives
│   │   │   ├── features/       # Feature modules
│   │   │   │   ├── inventory/
│   │   │   │   ├── locations/
│   │   │   │   └── reports/
│   │   │   └── layout/         # App shell, nav, sidebar
│   │   ├── assets/
│   │   └── styles/
│   │       ├── _variables.scss
│   │       ├── _theme.scss
│   │       └── styles.scss
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       └── router.py
│   │   ├── core/               # Config, security, dependencies
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   └── main.py
│   └── alembic/                # Migrations
└── docker-compose.yml
```

---

## Git Conventions

### Branch Naming

- `feature/` — New features (feature/add-barcode-scanning)
- `fix/` — Bug fixes (fix/stock-count-calculation)
- `refactor/` — Code refactoring (refactor/inventory-service)
- `docs/` — Documentation updates

### Commit Messages

Use conventional commits:

```
feat: add barcode scanning to inventory intake
fix: correct stock level calculation on transfer
refactor: extract inventory validation to service
docs: update API documentation for stock endpoints
chore: update dependencies
```

---

## API Response Standards

### Success Response

```json
{
  "data": {},
  "meta": {
    "timestamp": "2025-01-02T10:00:00Z",
    "requestId": "uuid"
  }
}
```

### Paginated Response

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "pageSize": 25,
    "totalItems": 150,
    "totalPages": 6
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "INVENTORY_NOT_FOUND",
    "message": "Inventory item with SKU 'ABC123' not found",
    "details": {}
  },
  "meta": {
    "timestamp": "2025-01-02T10:00:00Z",
    "requestId": "uuid"
  }
}
```
