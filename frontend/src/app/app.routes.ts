import { Routes } from '@angular/router';
import { InventoryListComponent } from './components/inventory-list/inventory-list.component';
import { LocationListComponent } from './features/locations/components/location-list/location-list.component';
import { CategoryListComponent } from './features/categories/components/category-list/category-list.component';

export const routes: Routes = [
  { path: '', redirectTo: '/inventory', pathMatch: 'full' },
  { path: 'inventory', component: InventoryListComponent },
  { path: 'locations', component: LocationListComponent },
  { path: 'categories', component: CategoryListComponent }
];
