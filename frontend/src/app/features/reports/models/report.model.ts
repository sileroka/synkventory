/**
 * Inventory Valuation Report Models
 */

export interface IValuationItemCategory {
  id: string;
  name: string;
  code: string;
}

export interface IValuationItemLocation {
  id: string;
  name: string;
  code: string;
}

export interface IValuationItem {
  id: string;
  sku: string;
  name: string;
  quantity: number;
  unitPrice: number;
  totalValue: number;
  category?: IValuationItemCategory;
  location?: IValuationItemLocation;
}

export interface ICategoryValuationSummary {
  categoryId?: string;
  categoryName: string;
  categoryCode?: string;
  itemCount: number;
  totalUnits: number;
  totalValue: number;
}

export interface ILocationValuationSummary {
  locationId?: string;
  locationName: string;
  locationCode?: string;
  itemCount: number;
  totalUnits: number;
  totalValue: number;
}

export interface IInventoryValuationReport {
  totalItems: number;
  totalUnits: number;
  totalValue: number;
  items: IValuationItem[];
  byCategory: ICategoryValuationSummary[];
  byLocation: ILocationValuationSummary[];
}

/**
 * Stock Movement Report Models
 */

export type MovementType = 'receive' | 'ship' | 'transfer' | 'adjust' | 'count';

export interface IMovementReportItem {
  id: string;
  name: string;
  sku: string;
}

export interface IMovementReportLocation {
  id: string;
  name: string;
  code: string;
}

export interface IStockMovementReportEntry {
  id: string;
  date: string;
  inventoryItem: IMovementReportItem;
  movementType: MovementType;
  quantity: number;
  fromLocation?: IMovementReportLocation;
  toLocation?: IMovementReportLocation;
  referenceNumber?: string;
  notes?: string;
  runningBalance: number;
}

export interface IStockMovementReportSummary {
  totalMovements: number;
  totalIn: number;
  totalOut: number;
  netChange: number;
}

export interface IStockMovementReport {
  summary: IStockMovementReportSummary;
  movements: IStockMovementReportEntry[];
}
