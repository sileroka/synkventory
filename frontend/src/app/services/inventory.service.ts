import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { IInventoryItem, IInventoryLocationQuantity, ILowStockAlert, InventoryStatus } from '../models/inventory-item.model';
import { IStockMovement, IStockMovementCreate } from '../models/stock-movement.model';
import { environment } from '../../environments/environment';
import {
  IDataResponse,
  IListResponse,
  IMessageResponse,
  IPaginationMeta
} from '../models/api-response.model';

export interface IInventoryListResult {
  items: IInventoryItem[];
  pagination: IPaginationMeta;
}

export interface ILocationQuantityResult {
  items: IInventoryLocationQuantity[];
  pagination: IPaginationMeta;
}

export interface ILowStockAlertResult {
  items: ILowStockAlert[];
  pagination: IPaginationMeta;
}

export interface IStockMovementResult {
  items: IStockMovement[];
  pagination: IPaginationMeta;
}

export interface IBulkOperationResult {
  successCount: number;
  failedCount: number;
  failedIds: string[];
}

export interface IInventoryFilters {
  search?: string;
  categoryIds?: string[];
  locationIds?: string[];
  statuses?: string[];
  sortField?: string;
  sortOrder?: number;
}

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private apiUrl = `${environment.apiUrl}/inventory`;
  private stockMovementsUrl = `${environment.apiUrl}/stock-movements`;

  constructor(private http: HttpClient) { }

  getItems(
    page: number = 1,
    pageSize: number = 25,
    filters?: IInventoryFilters
  ): Observable<IInventoryListResult> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    if (filters) {
      if (filters.search) {
        params = params.set('search', filters.search);
      }
      if (filters.categoryIds && filters.categoryIds.length > 0) {
        filters.categoryIds.forEach(id => {
          params = params.append('categoryIds', id);
        });
      }
      if (filters.locationIds && filters.locationIds.length > 0) {
        filters.locationIds.forEach(id => {
          params = params.append('locationIds', id);
        });
      }
      if (filters.statuses && filters.statuses.length > 0) {
        filters.statuses.forEach(status => {
          params = params.append('statuses', status);
        });
      }
      if (filters.sortField) {
        params = params.set('sortField', filters.sortField);
      }
      if (filters.sortOrder !== undefined) {
        params = params.set('sortOrder', filters.sortOrder.toString());
      }
    }

    return this.http.get<IListResponse<IInventoryItem>>(this.apiUrl, { params })
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  getItem(id: string): Observable<IInventoryItem> {
    return this.http.get<IDataResponse<IInventoryItem>>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.data));
  }

  getItemLocationQuantities(id: string): Observable<ILocationQuantityResult> {
    return this.http.get<IListResponse<IInventoryLocationQuantity>>(`${this.apiUrl}/${id}/locations`)
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  createItem(item: IInventoryItem): Observable<IInventoryItem> {
    return this.http.post<IDataResponse<IInventoryItem>>(this.apiUrl, item)
      .pipe(map(response => response.data));
  }

  updateItem(id: string, item: Partial<IInventoryItem>): Observable<IInventoryItem> {
    return this.http.put<IDataResponse<IInventoryItem>>(`${this.apiUrl}/${id}`, item)
      .pipe(map(response => response.data));
  }

  deleteItem(id: string): Observable<string> {
    return this.http.delete<IMessageResponse>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.message));
  }

  bulkDelete(ids: string[]): Observable<IBulkOperationResult> {
    return this.http.post<IDataResponse<IBulkOperationResult>>(`${this.apiUrl}/bulk-delete`, { ids })
      .pipe(map(response => response.data));
  }

  bulkStatusUpdate(ids: string[], status: InventoryStatus): Observable<IBulkOperationResult> {
    return this.http.post<IDataResponse<IBulkOperationResult>>(`${this.apiUrl}/bulk-status-update`, { ids, status })
      .pipe(map(response => response.data));
  }

  quickAdjust(id: string, quantity: number, reason?: string): Observable<IInventoryItem> {
    return this.http.post<IDataResponse<IInventoryItem>>(`${this.apiUrl}/${id}/quick-adjust`, { quantity, reason })
      .pipe(map(response => response.data));
  }

  getLowStockAlerts(page: number = 1, pageSize: number = 100): Observable<ILowStockAlertResult> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    return this.http.get<IListResponse<ILowStockAlert>>(`${this.apiUrl}/alerts/low-stock`, { params })
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  getItemMovements(id: string, page: number = 1, pageSize: number = 10): Observable<IStockMovementResult> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    return this.http.get<IListResponse<IStockMovement>>(`${this.apiUrl}/${id}/movements`, { params })
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  createStockMovement(movement: IStockMovementCreate): Observable<IStockMovement> {
    return this.http.post<IDataResponse<IStockMovement>>(this.stockMovementsUrl, movement)
      .pipe(map(response => response.data));
  }
}
