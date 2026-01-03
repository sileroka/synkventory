import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AdminAuthService } from '../services/admin-auth.service';
import { TenantService } from '../services/tenant.service';
import { toObservable } from '@angular/core/rxjs-interop';
import { filter, map, take } from 'rxjs';

/**
 * Guard to ensure we're on the admin portal subdomain
 */
export const adminPortalGuard: CanActivateFn = () => {
  const tenantService = inject(TenantService);
  const router = inject(Router);

  if (!tenantService.isAdminPortal()) {
    // Not on admin subdomain, redirect to root
    window.location.href = 'https://synkventory.com';
    return false;
  }

  return true;
};

/**
 * Guard for admin authenticated routes
 */
export const adminAuthGuard: CanActivateFn = () => {
  const adminAuthService = inject(AdminAuthService);
  const router = inject(Router);

  // Always initialize first to check auth status
  return adminAuthService.initialize().pipe(
    map(user => {
      if (user) {
        return true;
      }
      router.navigate(['/admin/login']);
      return false;
    })
  );
};
/**
 * Guard for admin login page - redirect to dashboard if already authenticated
 */
export const adminNoAuthGuard: CanActivateFn = () => {
  const adminAuthService = inject(AdminAuthService);
  const router = inject(Router);

  // Always initialize first to check auth status
  return adminAuthService.initialize().pipe(
    map(user => {
      if (user) {
        // Already authenticated, go to dashboard
        router.navigate(['/admin/dashboard']);
        return false;
      }
      // Not authenticated, allow access to login page
      return true;
    })
  );
};

/**
 * Guard for super admin only routes
 */
export const superAdminGuard: CanActivateFn = () => {
  const adminAuthService = inject(AdminAuthService);
  const router = inject(Router);

  // Wait for loading to complete
  if (adminAuthService.isLoading()) {
    return toObservable(adminAuthService.isLoading).pipe(
      filter(loading => !loading),
      take(1),
      map(() => {
        if (adminAuthService.isSuperAdmin()) {
          return true;
        }
        router.navigate(['/admin/dashboard']);
        return false;
      })
    );
  }

  if (adminAuthService.isSuperAdmin()) {
    return true;
  }

  router.navigate(['/admin/dashboard']);
  return false;
};
