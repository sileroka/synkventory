import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError, switchMap } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { TenantService } from '../services/tenant.service';

/**
 * HTTP interceptor that:
 * 1. Adds withCredentials to all API requests (for cookies)
 * 2. Handles 401 responses by attempting token refresh
 * 3. Redirects to login on auth failure
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const tenantService = inject(TenantService);
  const router = inject(Router);

  // Add credentials for cookie-based auth
  const authReq = req.clone({
    withCredentials: true
  });

  // Check if this is an admin API request
  const isAdminRequest = req.url.includes('/admin/');

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle 401 Unauthorized
      if (error.status === 401) {
        // For admin API requests, don't interfere - let AdminAuthService handle it
        if (isAdminRequest) {
          return throwError(() => error);
        }

        // Don't try to refresh for login/logout/refresh/me endpoints
        if (req.url.includes('/auth/login') ||
            req.url.includes('/auth/logout') ||
            req.url.includes('/auth/refresh') ||
            req.url.includes('/auth/me')) {
          authService.clearAuth();
          // Only redirect if not on admin portal
          if (!tenantService.isAdminPortal()) {
            router.navigate(['/login']);
          }
          return throwError(() => error);
        }

        // Try to refresh the token
        return authService.refreshToken().pipe(
          switchMap(() => {
            // Retry the original request
            return next(authReq);
          }),
          catchError((refreshError) => {
            // Refresh failed, redirect to login
            authService.clearAuth();
            if (!tenantService.isAdminPortal()) {
              router.navigate(['/login']);
            }
            return throwError(() => refreshError);
          })
        );
      }

      // Handle 404 for auth/me (happens when no subdomain/tenant)
      if (error.status === 404 && req.url.includes('/auth/me') && !isAdminRequest) {
        authService.clearAuth();
        if (!tenantService.isAdminPortal()) {
          router.navigate(['/login']);
        }
        return throwError(() => error);
      }

      return throwError(() => error);
    })
  );
};
