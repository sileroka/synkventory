import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Auth guard to protect routes that require authentication.
 * Redirects to /login if user is not authenticated.
 */
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Wait for auth check to complete
  if (authService.isLoading()) {
    // Could show loading indicator or wait
    return true;
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

  if (authService.isLoading()) {
    return true;
  }

  if (authService.isAuthenticated()) {
    router.navigate(['/dashboard']);
    return false;
  }

  return true;
};
