export enum InventoryStatus {
  IN_STOCK = 'in_stock',
  LOW_STOCK = 'low_stock',
  OUT_OF_STOCK = 'out_of_stock',
  ON_ORDER = 'on_order',
  DISCONTINUED = 'discontinued'
}

export interface IRelatedCategory {
  id: string;
  name: string;
}

export interface IRelatedLocation {
  id: string;
  name: string;
  code?: string;
}

export interface IInventoryLocationQuantity {
  inventoryItemId: string;
  locationId: string;
  quantity: number;
  binLocation?: string | null;
  location?: IRelatedLocation | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface IInventoryItem {
  id?: string;
  name: string;
  sku: string;
  description?: string;
  quantity: number;
  reorderPoint: number;
  unitPrice: number;
  status: InventoryStatus;
  categoryId?: string | null;
  locationId?: string | null;
  category?: IRelatedCategory | null;
  location?: IRelatedLocation | null;
  imageKey?: string | null;
  imageUrl?: string | null;
  customAttributes?: Record<string, any> | null;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface ILowStockAlert {
  id: string;
  name: string;
  sku: string;
  quantity: number;
  reorderPoint: number;
  suggestedOrderQuantity: number;
  status: InventoryStatus;
  category?: IRelatedCategory | null;
  location?: IRelatedLocation | null;
}
