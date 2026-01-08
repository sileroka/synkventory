# Frontend Lot/Serial Number Tracking Guide

## Overview

The Synkventory frontend provides comprehensive lot and serial number tracking capabilities integrated throughout the inventory management interface. Users can create, manage, and track lots from the inventory detail view, stock movements, and purchase order receiving workflows.

## Features

### 1. **Lot Management**

- Create new lots with lot numbers and serial numbers
- Edit existing lot information
- Delete lots
- Filter by location and expiration status
- Sort by creation date, expiration date, or lot number
- View lot history and expiration warnings

### 2. **Integration Points**

- **Inventory Item Detail**: Dedicated "Lots" tab for lot management
- **Stock Movements**: Optional lot selection when transferring inventory
- **Purchase Orders**: Receive items with lot information captured inline

### 3. **Expiration Tracking**

- Automatic expiration status indicators (Active, Expiring Soon, Expired)
- Color-coded severity badges
- Filter to exclude expired lots

---

## Architecture

### Components

#### **LotDialogComponent** (`lot-dialog.component.ts`)

Modal dialog for creating and editing lots.

**Features:**

- Form validation for required fields (lot number, quantity)
- Unique lot number validation per tenant
- Optional serial number, expiration date, manufacture date, and location
- Location dropdown with available warehouses
- Error handling with user-friendly messages

**Inputs:**

- `lot`: Existing lot for edit mode (optional)
- `itemId`: Required inventory item ID

**Example Usage:**

```typescript
this.dialogRef = this.dialogService.open(LotDialogComponent, {
  width: "100%",
  maxWidth: "600px",
  data: { itemId: this.item.id },
});

this.dialogRef.onClose.subscribe((result: IItemLot | undefined) => {
  if (result) {
    // Handle success
  }
});
```

#### **LotListTableComponent** (`lot-list-table.component.ts`)

Paginated table displaying all lots for an inventory item.

**Features:**

- Lazy-loaded pagination (25 items per page)
- Real-time filtering by location
- Sort options: Created Date, Expiration Date, Lot Number
- Toggle to include/exclude expired lots
- Expiration status indicators with color coding
- Edit and delete actions with confirmation dialogs

**Inputs:**

- `itemId`: Required inventory item ID

**Data Display:**
| Column | Purpose |
|--------|---------|
| Lot Number | Identifies the lot (includes serial number if present) |
| Quantity | Units in this lot |
| Manufacture | Production date |
| Expiration | Expiration date with status badge |
| Location | Current storage location |
| Created | Timestamp of lot creation |
| Actions | Edit/Delete buttons |

#### **ItemLotService** (`item-lot.service.ts`)

HTTP service for lot API operations.

**Methods:**

```typescript
// Get lots for an item with filtering and pagination
getLotsForItem(
  itemId: string,
  page?: number,
  pageSize?: number,
  filters?: ILotFilters
): Observable<IListResponse<IItemLot>>

// Get a single lot by ID
getLotById(lotId: string): Observable<IDataResponse<IItemLot>>

// Create a new lot
createLot(itemId: string, lot: IItemLotCreate): Observable<IDataResponse<IItemLot>>

// Update an existing lot
updateLot(lotId: string, updates: IItemLotUpdate): Observable<IDataResponse<IItemLot>>

// Delete a lot
deleteLot(lotId: string): Observable<IMessageResponse>

// Validate lot number uniqueness
isLotNumberUnique(
  itemId: string,
  lotNumber: string,
  excludeLotId?: string
): Observable<{ unique: boolean }>
```

### Models

#### **IItemLot**

```typescript
interface IItemLot {
  id: string;
  itemId: string;
  lotNumber: string;
  serialNumber?: string | null;
  quantity: number;
  expirationDate?: string | null; // ISO 8601 date
  manufactureDate?: string | null; // ISO 8601 date
  locationId?: string | null;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy?: string;
  item?: IRelatedItem;
  location?: IRelatedLocation;
}
```

#### **ILotFilters**

```typescript
interface ILotFilters {
  locationId?: string;
  includeExpired?: boolean;
  orderBy?: "created_at" | "expiration_date" | "lot_number";
}
```

---

## User Workflows

### Workflow 1: Creating a Lot

1. **Navigate to Inventory Detail**

   - Click on an inventory item to view details
   - Click the "Lots" tab in the right panel

2. **Add New Lot**

   - Click "Add Lot" button
   - LotDialogComponent opens

3. **Fill Lot Information**

   - **Lot Number** (required): `LOT-2026-001`
   - **Serial Number** (optional): `SN-12345`
   - **Quantity** (required): `100`
   - **Manufacture Date** (optional): Date picker
   - **Expiration Date** (optional): Date picker (shows warning if past)
   - **Location** (optional): Dropdown of available locations

4. **Save**
   - Click "Create Lot"
   - Success message shown
   - Lot appears in table immediately

### Workflow 2: Transferring Stock by Lot

1. **Open Inventory Detail**

   - Navigate to inventory item detail page

2. **Click "Transfer" Button**

   - Transfer Dialog opens

3. **Select Source Location**

   - Choose "From Location"
   - Available lots for that location load automatically

4. **Select Lot (Optional)**

   - If lots exist, a "Lot/Serial" dropdown appears
   - Select specific lot to transfer, or leave blank to use any lot

5. **Complete Transfer**
   - Choose destination location
   - Enter quantity
   - Add notes if needed
   - Click "Transfer"

### Workflow 3: Receiving PO with Lots

1. **Open Purchase Order**

   - Navigate to purchase order detail

2. **Click "Receive Items"**

   - Receive Dialog opens with line items table

3. **Enter Quantities**

   - For each line item, enter "Receive Now" quantity

4. **Add Lot Information (Optional)**

   - For each item with quantity > 0, lot section appears
   - Click "Add Lot" button
   - Fill in lot details:
     - Lot Number (required)
     - Serial Number (optional)
     - Quantity for this lot
     - Manufacture/Expiration dates

5. **Receive Items**
   - Click "Receive Items" button
   - Lots are created automatically with received inventory
   - Success confirmation shown

### Workflow 4: Filtering and Viewing Lots

1. **Open Lot Management Tab**

   - In Inventory Detail → Lots tab

2. **Apply Filters**

   - **Location**: Filter lots by storage location
   - **Sort By**: Order by created date, expiration, or lot number
   - **Include Expired**: Toggle to show/hide expired lots

3. **View Details**

   - Table shows all lot information
   - Expiration badges color-coded:
     - **Green**: Active (expires > 30 days)
     - **Yellow**: Expiring Soon (expires ≤ 30 days)
     - **Red**: Expired (past expiration date)
     - **Blue**: No expiration

4. **Manage Lots**
   - Click edit icon to modify lot
   - Click delete icon to remove lot

---

## Integration with Existing Features

### Stock Movements

**File**: `inventory-detail.component.ts`

When transferring stock, lot selection is now available:

```typescript
// Load lots for the selected source location
onTransferFromLocationChange() {
  this.transferLotId = '';
  this.transferLotOptions = [];
  this.loadTransferLots();
}

// Save transfer with optional lot
saveTransfer() {
  const movement: IStockMovementCreate = {
    inventoryItemId: this.item.id,
    movementType: MovementType.TRANSFER,
    quantity: this.transferQuantity,
    fromLocationId: this.transferFromLocationId,
    toLocationId: this.transferToLocationId,
    lotId: this.transferLotId || undefined, // NEW
    notes: this.transferNotes || undefined
  };
  // ...
}
```

### Purchase Orders

**File**: `purchase-order-detail.component.ts`

Enhanced receive dialog captures lot information:

```typescript
// Initialize receive items with empty lots array
openReceiveDialog() {
  this.receiveItems = po.lineItems
    .filter(item => item.quantityOrdered > item.quantityReceived)
    .map(item => ({
      lineItemId: item.id,
      quantityReceived: 0,
      notes: '',
      lots: [] // NEW
    }));
}

// Add/remove lots from receive items
addLotToReceiveItem(itemIndex: number) {
  this.receiveItems[itemIndex].lots?.push({
    lotNumber: '',
    serialNumber: undefined,
    quantity: 1,
    expirationDate: undefined,
    manufactureDate: undefined
  });
}

removeLotFromReceiveItem(itemIndex: number, lotIndex: number) {
  this.receiveItems[itemIndex].lots?.splice(lotIndex, 1);
}
```

---

## Styling and UX

### Color Scheme

- **Primary Actions**: Teal (#0D9488)
- **Secondary Actions**: Coral (#F87171)
- **Success**: Green (#10B981)
- **Warning**: Amber (#F59E0B)
- **Danger/Error**: Red (#EF4444)
- **Info**: Indigo (#6366F1)

### Responsive Design

All components are mobile-responsive:

- Dialog max-width: 600px
- Table columns adapt for smaller screens
- Grid layout with responsive breakpoints (md, lg)

### Accessibility

- Form labels with required indicators (\*)
- Placeholder text for guidance
- Error messages in red with icons
- Keyboard navigation support
- Focus states on all interactive elements
- Disabled state for invalid actions

---

## Error Handling

### Common Errors and Solutions

| Error                             | Cause                           | Solution                            |
| --------------------------------- | ------------------------------- | ----------------------------------- |
| "Lot number already exists"       | Duplicate lot number for tenant | Use unique lot number               |
| "Quantity must be greater than 0" | Invalid quantity entered        | Enter positive number               |
| "Item not found"                  | Invalid item ID                 | Verify item exists                  |
| "Location not found"              | Invalid location ID             | Select valid location from dropdown |
| "Insufficient quantity"           | Transfer more than available    | Reduce transfer quantity            |

### User Feedback

- **Success**: Green toast notification (3 sec)
- **Error**: Red toast notification (5 sec) with error details
- **Warning**: Yellow toast notification (3 sec)
- **Loading**: Spinner shown during API calls

---

## Testing Guide

### Manual Testing Checklist

- [ ] Create lot with all fields
- [ ] Create lot with minimal fields
- [ ] Edit lot and verify changes save
- [ ] Delete lot and confirm removal
- [ ] Filter lots by location
- [ ] Filter lots by expiration status
- [ ] Sort lots by different columns
- [ ] Transfer stock with lot selection
- [ ] Receive PO with multiple lots
- [ ] Verify expiration status badges
- [ ] Test on mobile/tablet screens
- [ ] Verify error messages display correctly
- [ ] Test date validation (expiration date in past)

### E2E Test Scenarios

**Test 1: Complete Lot Lifecycle**

1. Create inventory item
2. Create lot for item
3. Edit lot details
4. View lot in table with filters
5. Delete lot
6. Confirm deletion

**Test 2: Stock Movement with Lots**

1. Create item with lots
2. Transfer stock specifying lot
3. Verify lot inventory updated
4. Check stock movement history

**Test 3: PO Receiving with Lots**

1. Create purchase order
2. Click "Receive Items"
3. Add multiple lots to single line item
4. Receive items
5. Verify lots created in inventory

---

## Performance Considerations

### Optimization

- **Lazy Loading**: Lots load on-demand with pagination
- **Debouncing**: Filter changes debounced (300ms)
- **Caching**: Location list cached in component
- **Virtual Scrolling**: Consider for > 1000 rows

### Data Transfer

- **Page Size**: 25 items default (configurable)
- **Filters**: Applied server-side for efficiency
- **Relationships**: Nested item/location data included in response

---

## Future Enhancements

1. **Lot Barcode Scanning**

   - Scan lot numbers to auto-populate fields
   - Barcode generation for printed labels

2. **Batch Operations**

   - Select multiple lots
   - Bulk edit (e.g., change expiration date)
   - Bulk delete with confirmation

3. **Lot History Timeline**

   - Track lot movements over time
   - Show all stock movements for a lot
   - Generate lot audit reports

4. **Expiration Alerts**

   - Dashboard widget showing expiring soon lots
   - Email notifications for approaching expiration
   - Automated reorder suggestions

5. **Advanced Lot Tracking**
   - Cost tracking per lot
   - Supplier information per lot
   - Recall management
   - Temperature/condition tracking for sensitive items

---

## API Reference

### Frontend → Backend Endpoints

```
GET    /api/v1/inventory/items/{itemId}/lots
POST   /api/v1/inventory/items/{itemId}/lots
PUT    /api/v1/inventory/lots/{lotId}
DELETE /api/v1/inventory/lots/{lotId}
GET    /api/v1/inventory/lots/{lotId}
```

For detailed API documentation, see [LOT_TRACKING_API.md](../docs/LOT_TRACKING_API.md).

---

## File Structure

```
frontend/src/app/
├── components/
│   ├── lot-dialog/
│   │   ├── lot-dialog.component.ts
│   │   ├── lot-dialog.component.html
│   │   └── lot-dialog.component.scss
│   └── lot-list-table/
│       ├── lot-list-table.component.ts
│       ├── lot-list-table.component.html
│       └── lot-list-table.component.scss
├── models/
│   ├── item-lot.model.ts
│   └── stock-movement.model.ts (updated)
├── services/
│   └── item-lot.service.ts
└── features/
    ├── inventory/
    │   └── inventory-detail.component.ts (updated)
    └── purchase-orders/
        └── purchase-order-detail.component.ts (updated)
```

---

## Deployment Checklist

- [ ] All components imported in respective modules
- [ ] API endpoint URLs configured in environment files
- [ ] Dialog service properly configured
- [ ] Form validation working on all fields
- [ ] Error messages user-friendly
- [ ] Loading states show spinners
- [ ] Date format consistent (ISO 8601)
- [ ] Responsive design tested on mobile
- [ ] Accessibility features verified
- [ ] Unit tests passing
- [ ] E2E tests passing
- [ ] Documentation updated
