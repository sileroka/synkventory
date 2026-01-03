import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of } from 'rxjs';
import { environment } from '../../../environments/environment';

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

export interface AdminLoginRequest {
  email: string;
  password: string;
}

export interface AdminLoginResponse {
  user: AdminUser;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class AdminAuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private _currentAdmin = signal<AdminUser | null>(null);
  private _isLoading = signal<boolean>(true);
  private _isInitialized = signal<boolean>(false);

  readonly currentAdmin = this._currentAdmin.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly isAuthenticated = computed(() => this._currentAdmin() !== null);
  readonly isSuperAdmin = computed(() => this._currentAdmin()?.is_super_admin ?? false);

  private get apiUrl(): string {
    return `${environment.apiUrl}/admin`;
  }

  /**
   * Initialize admin auth state by checking current session
   */
  initialize(): Observable<AdminUser | null> {
    if (this._isInitialized()) {
      this._isLoading.set(false);
      return of(this._currentAdmin());
    }

    this._isLoading.set(true);
    return this.http.get<AdminUser>(`${this.apiUrl}/auth/me`, { withCredentials: true }).pipe(
      tap(user => {
        this._currentAdmin.set(user);
        this._isLoading.set(false);
        this._isInitialized.set(true);
      }),
      catchError(() => {
        this._currentAdmin.set(null);
        this._isLoading.set(false);
        this._isInitialized.set(true);
        return of(null);
      })
    );
  }

  /**
   * Admin login
   */
  login(credentials: AdminLoginRequest): Observable<AdminLoginResponse> {
    return this.http.post<AdminLoginResponse>(
      `${this.apiUrl}/auth/login`,
      credentials,
      { withCredentials: true }
    ).pipe(
      tap(response => {
        this._currentAdmin.set(response.user);
      })
    );
  }

  /**
   * Admin logout
   */
  logout(): Observable<void> {
    return this.http.post<void>(
      `${this.apiUrl}/auth/logout`,
      {},
      { withCredentials: true }
    ).pipe(
      tap(() => {
        this._currentAdmin.set(null);
        this.router.navigate(['/admin/login']);
      })
    );
  }

  /**
   * Reset auth state (for testing)
   */
  reset(): void {
    this._currentAdmin.set(null);
    this._isLoading.set(false);
    this._isInitialized.set(false);
  }
}
