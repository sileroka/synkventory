import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../../environments/environment';
import { IAuditLogListResponse, IAuditLogFilters } from '../models/audit-log.model';

@Injectable({
  providedIn: 'root'
})
export class AdminAuditService {
  private http = inject(HttpClient);

  private get apiUrl(): string {
    return `${environment.apiUrl}/admin`;
  }

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
      if (filters.tenantId) {
        params = params.set('tenantId', filters.tenantId);
      }
      if (filters.userId) {
        params = params.set('userId', filters.userId);
      }
      if (filters.action) {
        params = params.set('action', filters.action);
      }
      if (filters.entityType) {
        params = params.set('entityType', filters.entityType);
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

    return this.http.get<IAuditLogListResponse>(
      `${this.apiUrl}/audit-logs`,
      { params, withCredentials: true }
    );
  }

  /**
   * Get list of distinct action types.
   */
  getActions(): Observable<string[]> {
    return this.http.get<string[]>(
      `${this.apiUrl}/audit-logs/actions`,
      { withCredentials: true }
    );
  }

  /**
   * Get list of distinct entity types.
   */
  getEntityTypes(): Observable<string[]> {
    return this.http.get<string[]>(
      `${this.apiUrl}/audit-logs/entity-types`,
      { withCredentials: true }
    );
  }
}
