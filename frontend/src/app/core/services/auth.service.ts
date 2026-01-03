import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  tenantId: string;
  isActive: boolean;
}

export interface LoginResponse {
  message: string;
  user: User;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiUrl = `${environment.apiUrl}/auth`;

  // Signals for reactive state
  private currentUserSignal = signal<User | null>(null);
  private isLoadingSignal = signal<boolean>(true);

  // Computed values
  readonly currentUser = this.currentUserSignal.asReadonly();
  readonly isAuthenticated = computed(() => !!this.currentUserSignal());
  readonly isLoading = this.isLoadingSignal.asReadonly();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    // Check auth status on service init
    this.checkAuthStatus();
  }

  /**
   * Check if user is currently authenticated by calling /auth/me
   */
  checkAuthStatus(): void {
    this.isLoadingSignal.set(true);
    this.http.get<{ data: User }>(`${this.apiUrl}/me`, { withCredentials: true })
      .pipe(
        tap(response => {
          this.currentUserSignal.set(response.data);
          this.isLoadingSignal.set(false);
        }),
        catchError(() => {
          this.currentUserSignal.set(null);
          this.isLoadingSignal.set(false);
          return of(null);
        })
      )
      .subscribe();
  }

  /**
   * Login with email and password
   */
  login(credentials: LoginRequest): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(
      `${this.apiUrl}/login`,
      credentials,
      { withCredentials: true }
    ).pipe(
      tap(response => {
        this.currentUserSignal.set(response.user);
      })
    );
  }

  /**
   * Logout - clear cookies and redirect to login
   */
  logout(): void {
    this.http.post(`${this.apiUrl}/logout`, {}, { withCredentials: true })
      .pipe(
        catchError(() => of(null))
      )
      .subscribe(() => {
        this.currentUserSignal.set(null);
        this.router.navigate(['/login']);
      });
  }

  /**
   * Refresh access token using refresh token cookie
   */
  refreshToken(): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.apiUrl}/refresh`,
      {},
      { withCredentials: true }
    );
  }

  /**
   * Clear user state (called on 401)
   */
  clearAuth(): void {
    this.currentUserSignal.set(null);
  }
}
