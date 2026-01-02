import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { InventoryService, ILowStockAlertResult } from '../../services/inventory.service';
import { ILowStockAlert, InventoryStatus } from '../../models/inventory-item.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    TableModule,
    TagModule,
    TooltipModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  lowStockCount: number = 0;
  lowStockAlerts: ILowStockAlert[] = [];
  loading: boolean = false;

  constructor(
    private inventoryService: InventoryService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadLowStockAlerts();
  }

  loadLowStockAlerts() {
    this.loading = true;
    this.inventoryService.getLowStockAlerts(1, 10).subscribe({
      next: (result: ILowStockAlertResult) => {
        this.lowStockAlerts = result.items;
        this.lowStockCount = result.pagination.totalItems;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  navigateToLowStock() {
    this.router.navigate(['/inventory'], { queryParams: { status: 'low_stock' } });
  }

  navigateToItem(id: string) {
    this.router.navigate(['/inventory'], { queryParams: { highlight: id } });
  }

  getStatusSeverity(status: InventoryStatus): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
    const severities: Record<InventoryStatus, 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'> = {
      [InventoryStatus.IN_STOCK]: 'success',
      [InventoryStatus.LOW_STOCK]: 'warn',
      [InventoryStatus.OUT_OF_STOCK]: 'danger',
      [InventoryStatus.ON_ORDER]: 'info',
      [InventoryStatus.DISCONTINUED]: 'secondary'
    };
    return severities[status] || 'info';
  }

  getStatusLabel(status: InventoryStatus): string {
    const labels: Record<InventoryStatus, string> = {
      [InventoryStatus.IN_STOCK]: 'In Stock',
      [InventoryStatus.LOW_STOCK]: 'Low Stock',
      [InventoryStatus.OUT_OF_STOCK]: 'Out of Stock',
      [InventoryStatus.ON_ORDER]: 'On Order',
      [InventoryStatus.DISCONTINUED]: 'Discontinued'
    };
    return labels[status] || status;
  }
}
