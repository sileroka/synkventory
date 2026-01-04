import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

// ----- Tenant Interfaces -----

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  user_count: number;
}

export interface TenantCreate {
  name: string;
  slug: string;
}

export interface TenantUpdate {
  name?: string;
  is_active?: boolean;
}

// ----- Tenant User Interfaces -----

export interface TenantUser {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TenantUserCreate {
  email: string;
  name: string;
  password: string;
  role: string;
}

export interface TenantUserUpdate {
  name?: string;
  role?: string;
  is_active?: boolean;
}

// ----- Admin User Interfaces -----

export interface AdminUser {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  is_super_admin: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface AdminUserCreate {
  email: string;
  name: string;
  password: string;
  is_super_admin: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AdminApiService {
  private http = inject(HttpClient);

  private get apiUrl(): string {
    return `${environment.apiUrl}/admin`;
  }

  // ----- Tenant Management -----

  getTenants(): Observable<Tenant[]> {
    return this.http.get<Tenant[]>(`${this.apiUrl}/tenants`, { withCredentials: true });
  }

  getTenant(tenantId: string): Observable<Tenant> {
    return this.http.get<Tenant>(`${this.apiUrl}/tenants/${tenantId}`, { withCredentials: true });
  }

  createTenant(data: TenantCreate): Observable<Tenant> {
    return this.http.post<Tenant>(`${this.apiUrl}/tenants`, data, { withCredentials: true });
  }

  updateTenant(tenantId: string, data: TenantUpdate): Observable<Tenant> {
    return this.http.patch<Tenant>(`${this.apiUrl}/tenants/${tenantId}`, data, { withCredentials: true });
  }

  deleteTenant(tenantId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/tenants/${tenantId}`, { withCredentials: true });
  }

  // ----- Tenant User Management -----

  getTenantUsers(tenantId: string): Observable<TenantUser[]> {
    return this.http.get<TenantUser[]>(`${this.apiUrl}/tenants/${tenantId}/users`, { withCredentials: true });
  }

  getTenantUser(tenantId: string, userId: string): Observable<TenantUser> {
    return this.http.get<TenantUser>(`${this.apiUrl}/tenants/${tenantId}/users/${userId}`, { withCredentials: true });
  }

  createTenantUser(tenantId: string, data: TenantUserCreate): Observable<TenantUser> {
    return this.http.post<TenantUser>(`${this.apiUrl}/tenants/${tenantId}/users`, data, { withCredentials: true });
  }

  updateTenantUser(tenantId: string, userId: string, data: TenantUserUpdate): Observable<TenantUser> {
    return this.http.patch<TenantUser>(`${this.apiUrl}/tenants/${tenantId}/users/${userId}`, data, { withCredentials: true });
  }

  deleteTenantUser(tenantId: string, userId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/tenants/${tenantId}/users/${userId}`, { withCredentials: true });
  }

  // ----- Admin User Management -----

  getAdminUsers(): Observable<AdminUser[]> {
    return this.http.get<AdminUser[]>(`${this.apiUrl}/admin-users`, { withCredentials: true });
  }

  createAdminUser(data: AdminUserCreate): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.apiUrl}/admin-users`, data, { withCredentials: true });
  }

  updateAdminUser(adminId: string, data: Partial<{ name: string; is_super_admin: boolean; is_active: boolean }>): Observable<AdminUser> {
    return this.http.patch<AdminUser>(`${this.apiUrl}/admin-users/${adminId}`, data, { withCredentials: true });
  }
}
