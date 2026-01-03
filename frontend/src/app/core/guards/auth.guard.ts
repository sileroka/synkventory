import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { toObservable } from '@angular/core/rxjs-interop';
import { filter, map, take } from 'rxjs';

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
 */
export const noAuthGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

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
