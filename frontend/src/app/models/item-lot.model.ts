export interface IRelatedItem {
  id: string;
  name: string;
  sku: string;
}

export interface IRelatedLocation {
  id: string;
  name: string;
  code?: string;
}

export interface IItemLot {
  id: string;
  itemId: string;
  lotNumber: string;
  serialNumber?: string | null;
  quantity: number;
  expirationDate?: string | null; // ISO 8601 date string
  manufactureDate?: string | null; // ISO 8601 date string
  locationId?: string | null;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy?: string;
  item?: IRelatedItem;
  location?: IRelatedLocation;
}

export interface IItemLotCreate {
  lotNumber: string;
  serialNumber?: string | null;
  quantity: number;
  expirationDate?: string | null;
  manufactureDate?: string | null;
  locationId?: string | null;
}

export interface IItemLotUpdate {
  lotNumber?: string;
  serialNumber?: string | null;
  quantity?: number;
  expirationDate?: string | null;
  manufactureDate?: string | null;
  locationId?: string | null;
}

export interface IItemLotListResult {
  items: IItemLot[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

export enum LotFilterMode {
  ACTIVE = 'active',
  EXPIRED = 'expired',
  ALL = 'all'
}

export interface ILotFilters {
  locationId?: string;
  includeExpired?: boolean;
  orderBy?: 'created_at' | 'expiration_date' | 'lot_number';
}
