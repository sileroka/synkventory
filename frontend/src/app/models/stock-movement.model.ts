export enum MovementType {
  RECEIVE = 'receive',
  SHIP = 'ship',
  TRANSFER = 'transfer',
  ADJUST = 'adjust',
  COUNT = 'count'
}

export interface IRelatedInventoryItem {
  id: string;
  name: string;
  sku: string;
}

export interface IRelatedLocation {
  id: string;
  name: string;
  code: string;
}

export interface IStockMovement {
  id: string;
  inventoryItemId: string;
  movementType: MovementType;
  quantity: number;
  fromLocationId?: string | null;
  toLocationId?: string | null;
  referenceNumber?: string | null;
  notes?: string | null;
  createdAt?: string;
  createdBy?: string | null;
  inventoryItem?: IRelatedInventoryItem | null;
  fromLocation?: IRelatedLocation | null;
  toLocation?: IRelatedLocation | null;
}

export interface IStockMovementCreate {
  inventoryItemId: string;
  movementType: MovementType;
  quantity: number;
  fromLocationId?: string | null;
  toLocationId?: string | null;
  referenceNumber?: string | null;
  notes?: string | null;
}
