import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface IAuditLog {
  id: string;
  tenantId: string;
  userId?: string;
  userEmail?: string;
  action: string;
  entityType: string;
  entityId?: string;
  entityName?: string;
  extraData?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  createdAt: string;
}

export interface IAuditLogListResponse {
  data: IAuditLog[];
  meta: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

export interface IAuditLogFilters {
  userId?: string;
  action?: string;
  entityType?: string;
  entityId?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
}

export interface IAuditLogSummary {
  totalLogs: number;
  uniqueUsers: number;
  actionCounts: Record<string, number>;
  entityTypeCounts: Record<string, number>;
  recentActivity: IAuditLog[];
}

export enum AuditAction {
  // Authentication
  LOGIN = 'LOGIN',
  LOGOUT = 'LOGOUT',
  LOGIN_FAILED = 'LOGIN_FAILED',
  PASSWORD_CHANGE = 'PASSWORD_CHANGE',
  PASSWORD_RESET = 'PASSWORD_RESET',

  // CRUD
  CREATE = 'CREATE',
  READ = 'READ',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',

  // Stock operations
  STOCK_RECEIVE = 'STOCK_RECEIVE',
  STOCK_SHIP = 'STOCK_SHIP',
  STOCK_TRANSFER = 'STOCK_TRANSFER',
  STOCK_ADJUST = 'STOCK_ADJUST',
  STOCK_COUNT = 'STOCK_COUNT',

  // Bulk operations
  BULK_DELETE = 'BULK_DELETE',
  BULK_UPDATE = 'BULK_UPDATE',
  BULK_IMPORT = 'BULK_IMPORT',
  BULK_EXPORT = 'BULK_EXPORT',

  // User management
  USER_ACTIVATE = 'USER_ACTIVATE',
  USER_DEACTIVATE = 'USER_DEACTIVATE',
  USER_LOCK = 'USER_LOCK',
  USER_UNLOCK = 'USER_UNLOCK',

  // Work Orders
  WORK_ORDER_CREATE = 'WORK_ORDER_CREATE',
  WORK_ORDER_START = 'WORK_ORDER_START',
  WORK_ORDER_COMPLETE = 'WORK_ORDER_COMPLETE',
  WORK_ORDER_CANCEL = 'WORK_ORDER_CANCEL',

  // Purchase Orders
  PURCHASE_ORDER_CREATE = 'PURCHASE_ORDER_CREATE',
  PURCHASE_ORDER_SUBMIT = 'PURCHASE_ORDER_SUBMIT',
  PURCHASE_ORDER_APPROVE = 'PURCHASE_ORDER_APPROVE',
  PURCHASE_ORDER_RECEIVE = 'PURCHASE_ORDER_RECEIVE',
  PURCHASE_ORDER_CANCEL = 'PURCHASE_ORDER_CANCEL',
}

/**
 * Action display labels for UI.
 */
export const ActionLabels: Record<string, string> = {
  [AuditAction.LOGIN]: 'User Login',
  [AuditAction.LOGOUT]: 'User Logout',
  [AuditAction.LOGIN_FAILED]: 'Failed Login',
  [AuditAction.PASSWORD_CHANGE]: 'Password Changed',
  [AuditAction.PASSWORD_RESET]: 'Password Reset',
  [AuditAction.CREATE]: 'Created',
  [AuditAction.READ]: 'Viewed',
  [AuditAction.UPDATE]: 'Updated',
  [AuditAction.DELETE]: 'Deleted',
  [AuditAction.STOCK_RECEIVE]: 'Stock Received',
  [AuditAction.STOCK_SHIP]: 'Stock Shipped',
  [AuditAction.STOCK_TRANSFER]: 'Stock Transferred',
  [AuditAction.STOCK_ADJUST]: 'Stock Adjusted',
  [AuditAction.STOCK_COUNT]: 'Stock Count',
  [AuditAction.BULK_DELETE]: 'Bulk Delete',
  [AuditAction.BULK_UPDATE]: 'Bulk Update',
  [AuditAction.BULK_IMPORT]: 'Bulk Import',
  [AuditAction.BULK_EXPORT]: 'Bulk Export',
  [AuditAction.USER_ACTIVATE]: 'User Activated',
  [AuditAction.USER_DEACTIVATE]: 'User Deactivated',
  [AuditAction.USER_LOCK]: 'User Locked',
  [AuditAction.USER_UNLOCK]: 'User Unlocked',
  [AuditAction.WORK_ORDER_CREATE]: 'Work Order Created',
  [AuditAction.WORK_ORDER_START]: 'Work Order Started',
  [AuditAction.WORK_ORDER_COMPLETE]: 'Work Order Completed',
  [AuditAction.WORK_ORDER_CANCEL]: 'Work Order Cancelled',
  [AuditAction.PURCHASE_ORDER_CREATE]: 'PO Created',
  [AuditAction.PURCHASE_ORDER_SUBMIT]: 'PO Submitted',
  [AuditAction.PURCHASE_ORDER_APPROVE]: 'PO Approved',
  [AuditAction.PURCHASE_ORDER_RECEIVE]: 'PO Received',
  [AuditAction.PURCHASE_ORDER_CANCEL]: 'PO Cancelled',
};

@Injectable({
  providedIn: 'root',
})
export class AuditLogService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/audit-logs`;

  /**
   * Get paginated audit logs with optional filtering.
   */
  getAuditLogs(
    page: number = 1,
    pageSize: number = 50,
    filters?: IAuditLogFilters
  ): Observable<IAuditLogListResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    if (filters) {
      if (filters.userId) {
        params = params.set('userId', filters.userId);
      }
      if (filters.action) {
        params = params.set('action', filters.action);
      }
      if (filters.entityType) {
        params = params.set('entityType', filters.entityType);
      }
      if (filters.entityId) {
        params = params.set('entityId', filters.entityId);
      }
      if (filters.startDate) {
        params = params.set('startDate', filters.startDate);
      }
      if (filters.endDate) {
        params = params.set('endDate', filters.endDate);
      }
      if (filters.search) {
        params = params.set('search', filters.search);
      }
    }

    return this.http.get<IAuditLogListResponse>(this.apiUrl, { params });
  }

  /**
   * Get list of distinct action types.
   */
  getActions(): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/actions`);
  }

  /**
   * Get list of distinct entity types.
   */
  getEntityTypes(): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/entity-types`);
  }

  /**
   * Get audit log summary/stats.
   */
  getSummary(startDate?: string, endDate?: string): Observable<IAuditLogSummary> {
    let params = new HttpParams();
    if (startDate) {
      params = params.set('startDate', startDate);
    }
    if (endDate) {
      params = params.set('endDate', endDate);
    }
    return this.http.get<IAuditLogSummary>(`${this.apiUrl}/summary`, { params });
  }
}
