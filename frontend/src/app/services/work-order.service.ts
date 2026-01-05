import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  IWorkOrder,
  IWorkOrderListItem,
  IWorkOrderCreate,
  IWorkOrderUpdate,
  IWorkOrderStatusUpdate,
  IWorkOrderProgressUpdate,
  IWorkOrderBuildRequest,
  IWorkOrderStats,
  WorkOrderStatus,
  WorkOrderPriority,
} from '../models/work-order.model';
import {
  IDataResponse,
  IListResponse,
  IMessageResponse,
  IPaginationMeta,
} from '../models/api-response.model';

export interface IWorkOrderListResult {
  items: IWorkOrderListItem[];
  pagination: IPaginationMeta;
}

export interface IWorkOrderFilters {
  status?: WorkOrderStatus;
  priority?: WorkOrderPriority;
  itemId?: string;
  assignedToId?: string;
  includeCompleted?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class WorkOrderService {
  private apiUrl = `${environment.apiUrl}/work-orders`;

  constructor(private http: HttpClient) { }

  /**
   * Get paginated list of work orders.
   */
  getWorkOrders(
    page: number = 1,
    pageSize: number = 25,
    filters?: IWorkOrderFilters
  ): Observable<IWorkOrderListResult> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    if (filters) {
      if (filters.status) {
        params = params.set('status', filters.status);
      }
      if (filters.priority) {
        params = params.set('priority', filters.priority);
      }
      if (filters.itemId) {
        params = params.set('item_id', filters.itemId);
      }
      if (filters.assignedToId) {
        params = params.set('assigned_to_id', filters.assignedToId);
      }
      if (filters.includeCompleted) {
        params = params.set('include_completed', 'true');
      }
    }

    return this.http.get<IListResponse<IWorkOrderListItem>>(this.apiUrl, { params })
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  /**
   * Get work order statistics.
   */
  getStats(): Observable<IWorkOrderStats> {
    return this.http.get<IDataResponse<IWorkOrderStats>>(`${this.apiUrl}/stats`)
      .pipe(map(response => response.data));
  }

  /**
   * Get a single work order by ID.
   */
  getWorkOrder(id: string): Observable<IWorkOrder> {
    return this.http.get<IDataResponse<IWorkOrder>>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.data));
  }

  /**
   * Create a new work order.
   */
  createWorkOrder(data: IWorkOrderCreate): Observable<IWorkOrder> {
    const payload = {
      item_id: data.itemId,
      quantity_ordered: data.quantityOrdered,
      priority: data.priority || WorkOrderPriority.NORMAL,
      due_date: data.dueDate,
      output_location_id: data.outputLocationId,
      assigned_to_id: data.assignedToId,
      description: data.description,
      notes: data.notes,
    };
    return this.http.post<IDataResponse<IWorkOrder>>(this.apiUrl, payload)
      .pipe(map(response => response.data));
  }

  /**
   * Update a work order.
   */
  updateWorkOrder(id: string, data: IWorkOrderUpdate): Observable<IWorkOrder> {
    const payload: Record<string, unknown> = {};
    if (data.quantityOrdered !== undefined) payload['quantity_ordered'] = data.quantityOrdered;
    if (data.priority !== undefined) payload['priority'] = data.priority;
    if (data.dueDate !== undefined) payload['due_date'] = data.dueDate;
    if (data.outputLocationId !== undefined) payload['output_location_id'] = data.outputLocationId;
    if (data.assignedToId !== undefined) payload['assigned_to_id'] = data.assignedToId;
    if (data.description !== undefined) payload['description'] = data.description;
    if (data.notes !== undefined) payload['notes'] = data.notes;
    
    return this.http.put<IDataResponse<IWorkOrder>>(`${this.apiUrl}/${id}`, payload)
      .pipe(map(response => response.data));
  }

  /**
   * Update work order status.
   */
  updateStatus(id: string, data: IWorkOrderStatusUpdate): Observable<IWorkOrder> {
    return this.http.put<IDataResponse<IWorkOrder>>(`${this.apiUrl}/${id}/status`, data)
      .pipe(map(response => response.data));
  }

  /**
   * Record production progress.
   */
  recordProgress(id: string, data: IWorkOrderProgressUpdate): Observable<IWorkOrder> {
    const payload = {
      quantity_completed: data.quantityCompleted,
      quantity_scrapped: data.quantityScrapped || 0,
      notes: data.notes,
    };
    return this.http.put<IDataResponse<IWorkOrder>>(`${this.apiUrl}/${id}/progress`, payload)
      .pipe(map(response => response.data));
  }

  /**
   * Build assemblies for a work order (consumes components).
   */
  buildFromWorkOrder(id: string, data: IWorkOrderBuildRequest): Observable<IWorkOrder> {
    return this.http.post<IDataResponse<IWorkOrder>>(`${this.apiUrl}/${id}/build`, data)
      .pipe(map(response => response.data));
  }

  /**
   * Delete a work order (only draft or cancelled).
   */
  deleteWorkOrder(id: string): Observable<string> {
    return this.http.delete<IMessageResponse>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.message));
  }

  /**
   * Get work orders for a specific item.
   */
  getWorkOrdersForItem(itemId: string, includeCompleted: boolean = false): Observable<IWorkOrderListItem[]> {
    let params = new HttpParams();
    if (includeCompleted) {
      params = params.set('include_completed', 'true');
    }
    return this.http.get<IListResponse<IWorkOrderListItem>>(`${this.apiUrl}/item/${itemId}`, { params })
      .pipe(map(response => response.data));
  }
}
