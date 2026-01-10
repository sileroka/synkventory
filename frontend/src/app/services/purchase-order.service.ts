import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { environment } from '../../environments/environment';
import {
  IPurchaseOrder,
  IPurchaseOrderListItem,
  IPurchaseOrderCreate,
  IPurchaseOrderUpdate,
  IPurchaseOrderStats,
  ILowStockSuggestion,
  IReceiveItemsRequest,
  IPurchaseOrderLineItemCreate,
  IPurchaseOrderLineItem,
} from '../models/purchase-order.model';

interface ApiResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
}

interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

export interface IPurchaseOrderFilters {
  page?: number;
  pageSize?: number;
  status?: string;
  priority?: string;
  includeReceived?: boolean;
  supplierName?: string;
  supplierId?: string;
}

@Injectable({
  providedIn: 'root',
})
export class PurchaseOrderService {
  private readonly apiUrl = `${environment.apiUrl}/purchase-orders`;

  constructor(private http: HttpClient) {}

  /**
   * Get paginated list of purchase orders.
   */
  getPurchaseOrders(
    filters: IPurchaseOrderFilters = {}
  ): Observable<{ items: IPurchaseOrderListItem[]; total: number; page: number; pageSize: number }> {
    let params = new HttpParams();

    if (filters.page) params = params.set('page', filters.page.toString());
    if (filters.pageSize) params = params.set('page_size', filters.pageSize.toString());
    if (filters.status) params = params.set('status', filters.status);
    if (filters.priority) params = params.set('priority', filters.priority);
    if (filters.includeReceived) params = params.set('include_received', 'true');
    if (filters.supplierName) params = params.set('supplier_name', filters.supplierName);
    if (filters.supplierId) params = params.set('supplier_id', filters.supplierId);

    return this.http
      .get<PaginatedResponse<IPurchaseOrderListItem>>(this.apiUrl, { params })
      .pipe(
        map((response) => ({
          items: response.data,
          total: response.meta.totalItems,
          page: response.meta.page,
          pageSize: response.meta.pageSize,
        }))
      );
  }

  /**
   * Get a single purchase order by ID.
   */
  getPurchaseOrder(id: string): Observable<IPurchaseOrder> {
    return this.http
      .get<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}`)
      .pipe(map((response) => response.data));
  }

  /**
   * Get a single purchase order by ID (alias for getPurchaseOrder).
   */
  getById(id: string): Observable<ApiResponse<IPurchaseOrder>> {
    return this.http.get<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}`);
  }

  /**
   * Create a new purchase order.
   */
  createPurchaseOrder(data: IPurchaseOrderCreate): Observable<IPurchaseOrder> {
    return this.http
      .post<ApiResponse<IPurchaseOrder>>(this.apiUrl, data)
      .pipe(map((response) => response.data));
  }

  /**
   * Update a purchase order.
   */
  updatePurchaseOrder(id: string, data: IPurchaseOrderUpdate): Observable<IPurchaseOrder> {
    return this.http
      .put<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}`, data)
      .pipe(map((response) => response.data));
  }

  /**
   * Delete a purchase order.
   */
  deletePurchaseOrder(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  /**
   * Update purchase order status.
   */
  updateStatus(id: string, status: string, notes?: string): Observable<IPurchaseOrder> {
    return this.http
      .put<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}/status`, { status, notes })
      .pipe(map((response) => response.data));
  }

  /**
   * Submit purchase order for approval.
   */
  submit(id: string): Observable<ApiResponse<IPurchaseOrder>> {
    return this.http.put<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}/status`, { status: 'pending_approval' });
  }

  /**
   * Approve a purchase order.
   */
  approve(id: string): Observable<ApiResponse<IPurchaseOrder>> {
    return this.http.put<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}/status`, { status: 'approved' });
  }

  /**
   * Mark purchase order as ordered.
   */
  order(id: string): Observable<ApiResponse<IPurchaseOrder>> {
    return this.http.put<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}/status`, { status: 'ordered' });
  }

  /**
   * Cancel a purchase order.
   */
  cancel(id: string, reason?: string): Observable<ApiResponse<IPurchaseOrder>> {
    return this.http.put<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}/status`, { status: 'cancelled', notes: reason });
  }

  /**
   * Update a purchase order (alias for updatePurchaseOrder).
   */
  update(id: string, data: IPurchaseOrderUpdate): Observable<ApiResponse<IPurchaseOrder>> {
    return this.http.put<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}`, data);
  }

  /**
   * Delete a purchase order (alias for deletePurchaseOrder).
   */
  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  /**
   * Receive items on a purchase order.
   */
  receiveItems(id: string, data: IReceiveItemsRequest): Observable<IPurchaseOrder> {
    return this.http
      .post<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}/receive`, data)
      .pipe(map((response) => response.data));
  }

  /**
   * Receive items on a purchase order (returns full response).
   */
  receive(id: string, items: Array<{ lineItemId: string; quantityReceived: number; notes?: string }>): Observable<ApiResponse<IPurchaseOrder>> {
    return this.http.post<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/${id}/receive`, { items });
  }

  /**
   * Add a line item to a purchase order.
   */
  addLineItem(poId: string, data: IPurchaseOrderLineItemCreate): Observable<IPurchaseOrderLineItem> {
    return this.http
      .post<ApiResponse<IPurchaseOrderLineItem>>(`${this.apiUrl}/${poId}/line-items`, data)
      .pipe(map((response) => response.data));
  }

  /**
   * Remove a line item from a purchase order.
   */
  removeLineItem(poId: string, lineItemId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${poId}/line-items/${lineItemId}`);
  }

  /**
   * Get purchase order statistics.
   */
  getStats(): Observable<IPurchaseOrderStats> {
    return this.http
      .get<ApiResponse<IPurchaseOrderStats>>(`${this.apiUrl}/stats`)
      .pipe(map((response) => response.data));
  }

  /**
   * Get low stock suggestions for reordering.
   */
  getLowStockSuggestions(
    limit: number = 50,
    leadTimeDays?: number,
    safetyStock?: number
  ): Observable<ILowStockSuggestion> {
    let params = new HttpParams().set('limit', limit.toString());
    if (leadTimeDays !== undefined) {
      params = params.set('lead_time_days', leadTimeDays.toString());
    }
    if (safetyStock !== undefined) {
      params = params.set('safety_stock', safetyStock.toString());
    }
    return this.http
      .get<ApiResponse<ILowStockSuggestion>>(`${this.apiUrl}/low-stock`, { params })
      .pipe(map((response) => response.data));
  }

  /**
   * Create a purchase order from selected low stock items.
   */
  createFromLowStock(itemIds: string[], supplierName?: string): Observable<IPurchaseOrder> {
    let params = new HttpParams();
    if (supplierName) params = params.set('supplier_name', supplierName);

    return this.http
      .post<ApiResponse<IPurchaseOrder>>(`${this.apiUrl}/from-low-stock`, itemIds, { params })
      .pipe(map((response) => response.data));
  }

  /**
   * Get purchase orders for a specific item.
   */
  getPurchaseOrdersForItem(
    itemId: string,
    includeReceived: boolean = false
  ): Observable<IPurchaseOrderListItem[]> {
    let params = new HttpParams();
    if (includeReceived) params = params.set('include_received', 'true');

    return this.http
      .get<ApiResponse<IPurchaseOrderListItem[]>>(`${this.apiUrl}/for-item/${itemId}`, { params })
      .pipe(map((response) => response.data));
  }
}
