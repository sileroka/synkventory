import { inject } from '@angular/core';
import { Router, CanActivateFn, ActivatedRouteSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { TenantService } from '../services/tenant.service';
import { toObservable } from '@angular/core/rxjs-interop';
import { filter, map, take } from 'rxjs';
import { UserRole } from '../../models/user.model';

/**
 * Auth guard to protect routes that require authentication.
 * Redirects to /login if user is not authenticated.
 */
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // If still loading, wait for it to complete
  if (authService.isLoading()) {
    return toObservable(authService.isLoading).pipe(
      filter(loading => !loading),
      take(1),
      map(() => {
        if (authService.isAuthenticated()) {
          return true;
        }
        router.navigate(['/login']);
        return false;
      })
    );
  }

  if (authService.isAuthenticated()) {
    return true;
  }

  // Not authenticated, redirect to login
  router.navigate(['/login']);
  return false;
};

/**
 * Guard for login page - redirects to dashboard if already authenticated
 * Also redirects to admin login if on admin portal
 */
export const noAuthGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const tenantService = inject(TenantService);
  const router = inject(Router);

  // If on admin portal, redirect to admin login page
  if (tenantService.isAdminPortal()) {
    router.navigate(['/admin/login']);
    return false;
  }

  // If still loading, wait for it to complete
  if (authService.isLoading()) {
    return toObservable(authService.isLoading).pipe(
      filter(loading => !loading),
      take(1),
      map(() => {
        if (authService.isAuthenticated()) {
          router.navigate(['/dashboard']);
          return false;
        }
        return true;
      })
    );
  }

  if (authService.isAuthenticated()) {
    router.navigate(['/dashboard']);
    return false;
  }

  return true;
};

/**
 * Guard for landing page - only show on root domain, redirect to dashboard/login on subdomains
 */
export const landingGuard: CanActivateFn = () => {
  const tenantService = inject(TenantService);
  const authService = inject(AuthService);
  const router = inject(Router);

  // If on admin portal, redirect to admin login
  if (tenantService.isAdminPortal()) {
    router.navigate(['/admin/login']);
    return false;
  }

  // If on a subdomain (tenant site), redirect to dashboard or login
  if (tenantService.isSubdomain()) {
    // Wait for auth to load
    if (authService.isLoading()) {
      return toObservable(authService.isLoading).pipe(
        filter(loading => !loading),
        take(1),
        map(() => {
          if (authService.isAuthenticated()) {
            router.navigate(['/dashboard']);
          } else {
            router.navigate(['/login']);
          }
          return false;
        })
      );
    }

    if (authService.isAuthenticated()) {
      router.navigate(['/dashboard']);
    } else {
      router.navigate(['/login']);
    }
    return false;
  }

  // On root domain, show landing page
  return true;
};

/**
 * Role-based guard factory.
 * Usage: canActivate: [roleGuard([UserRole.ADMIN, UserRole.MANAGER])]
 *
 * Pass required roles via route data: { roles: [UserRole.ADMIN, UserRole.MANAGER] }
 */
export const roleGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const allowedRoles: UserRole[] = route.data['roles'] || [];

  const checkRole = (): boolean => {
    if (!authService.isAuthenticated()) {
      router.navigate(['/login']);
      return false;
    }

    const currentUser = authService.currentUser();
    if (!currentUser) {
      router.navigate(['/login']);
      return false;
    }

    if (allowedRoles.length === 0) {
      return true;
    }

    if (allowedRoles.includes(currentUser.role as UserRole)) {
      return true;
    }

    // Insufficient permissions - redirect to dashboard
    router.navigate(['/dashboard']);
    return false;
  };

  // If still loading, wait for it to complete
  if (authService.isLoading()) {
    return toObservable(authService.isLoading).pipe(
      filter(loading => !loading),
      take(1),
      map(() => checkRole())
    );
  }

  return checkRole();
};
