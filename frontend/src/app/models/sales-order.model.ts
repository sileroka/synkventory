export enum SalesOrderStatus {
  DRAFT = 'draft',
  CONFIRMED = 'confirmed',
  CANCELLED = 'cancelled',
  SHIPPED = 'shipped',
}

export enum SalesOrderPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
}

export interface ISalesOrderLineItem {
  id: string;
  itemId: string;
  sku: string;
  name: string;
  quantityOrdered: number;
  quantityShipped: number;
  unitPrice: number;
}

export interface ISalesOrderListItem {
  id: string;
  orderNumber: string;
  status: SalesOrderStatus;
  priority?: SalesOrderPriority;
  customerId: string;
  customerName: string;
  createdAt: string;
  updatedAt: string;
  subtotal?: number;
  total?: number;
}

export interface ISalesOrderDetail extends ISalesOrderListItem {
  notes?: string;
  lineItems: ISalesOrderLineItem[];
}

export interface ISalesOrderCreate {
  customerId: string;
  priority?: SalesOrderPriority;
  notes?: string;
  lineItems?: Array<{ itemId: string; quantity: number; unitPrice?: number }>;
}

export interface ISalesOrderUpdate {
  priority?: SalesOrderPriority;
  notes?: string;
}

export interface IShipItemsRequest {
  items: Array<{ lineItemId: string; quantity: number }>;
}

export interface IListQuery {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: SalesOrderStatus;
  customerId?: string;
}

export interface IListResult<T> {
  items: T[];
  total: number;
}
