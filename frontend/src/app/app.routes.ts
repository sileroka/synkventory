import { Routes, CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { InventoryListComponent } from './components/inventory-list/inventory-list.component';
import { InventoryDetailComponent } from './components/inventory-detail/inventory-detail.component';
import { LocationListComponent } from './features/locations/components/location-list/location-list.component';
import { CategoryListComponent } from './features/categories/components/category-list/category-list.component';
import { InventoryValuationComponent } from './features/reports/components/inventory-valuation/inventory-valuation.component';
import { StockMovementReportComponent } from './features/reports/components/stock-movement-report/stock-movement-report.component';
import { LoginComponent } from './features/auth/login/login.component';
import { UserListComponent } from './features/users/user-list.component';
import { LandingComponent } from './features/landing/landing.component';
import { BomListComponent } from './features/bill-of-materials/bom-list.component';
import { WorkOrderListComponent } from './features/work-orders/work-order-list.component';
import { WorkOrderDetailComponent } from './features/work-orders/work-order-detail.component';
import { authGuard, noAuthGuard, roleGuard, landingGuard } from './core/guards/auth.guard';
import { adminAuthGuard, adminNoAuthGuard, adminPortalGuard, superAdminGuard } from './core/guards/admin.guard';
import { UserRole } from './models/user.model';
import { TenantService } from './core/services/tenant.service';

// Admin components
import { AdminLoginComponent } from './features/admin/login/admin-login.component';
import { AdminLayoutComponent } from './features/admin/layout/admin-layout.component';
import { AdminDashboardComponent } from './features/admin/dashboard/admin-dashboard.component';
import { TenantListComponent } from './features/admin/tenants/tenant-list.component';
import { TenantDetailComponent } from './features/admin/tenants/tenant-detail.component';
import { AdminUserListComponent } from './features/admin/admin-users/admin-user-list.component';
import { AdminAuditLogsComponent } from './features/admin/audit-logs/admin-audit-logs.component';

/**
 * Guard for catch-all route - redirects appropriately based on portal
 */
const catchAllGuard: CanActivateFn = () => {
  const tenantService = inject(TenantService);
  const router = inject(Router);

  if (tenantService.isAdminPortal()) {
    router.navigate(['/admin/login']);
  } else {
    router.navigate(['/login']);
  }
  return false;
};

export const routes: Routes = [
  // Landing page (root domain only) - also handles redirect for admin portal
  { path: '', component: LandingComponent, canActivate: [landingGuard], pathMatch: 'full' },

  // Public routes
  { path: 'login', component: LoginComponent, canActivate: [noAuthGuard] },

  // Protected routes
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'inventory', component: InventoryListComponent, canActivate: [authGuard] },
  // Special inventory routes - must be BEFORE :id wildcard
  { path: 'inventory/new', redirectTo: 'inventory', pathMatch: 'full' },
  { path: 'inventory/import', redirectTo: 'inventory', pathMatch: 'full' },
  { path: 'inventory/:id', component: InventoryDetailComponent, canActivate: [authGuard] },
  { path: 'bill-of-materials', component: BomListComponent, canActivate: [authGuard] },
  { path: 'work-orders', component: WorkOrderListComponent, canActivate: [authGuard] },
  { path: 'work-orders/:id', component: WorkOrderDetailComponent, canActivate: [authGuard] },
  { path: 'locations', component: LocationListComponent, canActivate: [authGuard] },
  { path: 'locations/new', redirectTo: 'locations', pathMatch: 'full' },
  { path: 'categories', component: CategoryListComponent, canActivate: [authGuard] },
  // Stock movements routes
  { path: 'stock-movements', redirectTo: 'reports/movements', pathMatch: 'full' },
  { path: 'stock-movements/receive', redirectTo: 'reports/movements', pathMatch: 'full' },
  { path: 'stock-movements/transfer', redirectTo: 'reports/movements', pathMatch: 'full' },
  { path: 'reports/valuation', component: InventoryValuationComponent, canActivate: [authGuard] },
  { path: 'reports/movements', component: StockMovementReportComponent, canActivate: [authGuard] },

  // Settings routes (Admin/Manager only)
  {
    path: 'settings/custom-fields',
    loadComponent: () => import('./features/settings/custom-fields/custom-fields.component').then(m => m.CustomFieldsComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.MANAGER] }
  },

  // Admin/Manager only routes (tenant-level)
  {
    path: 'users',
    component: UserListComponent,
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.MANAGER] }
  },

  // Admin Portal routes (admin.synkventory.com)
  { path: 'admin/login', component: AdminLoginComponent, canActivate: [adminNoAuthGuard] },
  {
    path: 'admin',
    component: AdminLayoutComponent,
    canActivate: [adminAuthGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: AdminDashboardComponent },
      { path: 'tenants', component: TenantListComponent },
      { path: 'tenants/:id', component: TenantDetailComponent },
      { path: 'audit-logs', component: AdminAuditLogsComponent },
      { path: 'admins', component: AdminUserListComponent, canActivate: [superAdminGuard] },
    ]
  },

  // Catch-all redirect - handled by a guard that checks portal type
  { path: '**', canActivate: [catchAllGuard], component: LoginComponent }
];
