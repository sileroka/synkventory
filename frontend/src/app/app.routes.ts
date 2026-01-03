import { Routes } from '@angular/router';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { InventoryListComponent } from './components/inventory-list/inventory-list.component';
import { InventoryDetailComponent } from './components/inventory-detail/inventory-detail.component';
import { LocationListComponent } from './features/locations/components/location-list/location-list.component';
import { CategoryListComponent } from './features/categories/components/category-list/category-list.component';
import { InventoryValuationComponent } from './features/reports/components/inventory-valuation/inventory-valuation.component';
import { StockMovementReportComponent } from './features/reports/components/stock-movement-report/stock-movement-report.component';
import { LoginComponent } from './features/auth/login/login.component';
import { authGuard, noAuthGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  // Public routes
  { path: 'login', component: LoginComponent, canActivate: [noAuthGuard] },

  // Protected routes
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'inventory', component: InventoryListComponent, canActivate: [authGuard] },
  { path: 'inventory/:id', component: InventoryDetailComponent, canActivate: [authGuard] },
  { path: 'locations', component: LocationListComponent, canActivate: [authGuard] },
  { path: 'categories', component: CategoryListComponent, canActivate: [authGuard] },
  { path: 'reports/valuation', component: InventoryValuationComponent, canActivate: [authGuard] },
  { path: 'reports/movements', component: StockMovementReportComponent, canActivate: [authGuard] },

  // Catch-all redirect to login
  { path: '**', redirectTo: '/login' }
];
