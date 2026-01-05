import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

// PrimeNG Modules
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { CardModule } from 'primeng/card';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

import { BomService } from '../../services/bom.service';
import { InventoryService } from '../../services/inventory.service';
import { IInventoryItem, InventoryStatus } from '../../models/inventory-item.model';

interface IAssemblyItem extends IInventoryItem {
  componentCount?: number;
}

@Component({
  selector: 'app-bom-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    TooltipModule,
    TagModule,
    CardModule,
    ProgressSpinnerModule,
    ToastModule,
  ],
  providers: [MessageService],
  template: `
    <div class="bom-list-container">
      <div class="page-header">
        <div class="header-content">
          <h1>
            <i class="pi pi-sitemap mr-2"></i>
            Bill of Materials
          </h1>
          <p class="text-muted">Manage assemblies and their component relationships</p>
        </div>
      </div>

      <p-card>
        <div class="toolbar mb-3">
          <div class="search-box">
            <span class="p-input-icon-left">
              <i class="pi pi-search"></i>
              <input
                type="text"
                pInputText
                [(ngModel)]="searchTerm"
                (input)="onSearch()"
                placeholder="Search assemblies..."
                class="w-full"
              />
            </span>
          </div>
        </div>

        @if (isLoading()) {
          <div class="loading-container">
            <p-progressSpinner strokeWidth="4" />
            <p>Loading assemblies...</p>
          </div>
        } @else if (filteredAssemblies().length === 0) {
          <div class="empty-state">
            <i class="pi pi-sitemap empty-icon"></i>
            <h3>No Assemblies Found</h3>
            @if (searchTerm) {
              <p>No assemblies match your search criteria.</p>
            } @else {
              <p>Items with Bills of Materials will appear here.</p>
              <p class="hint">To create an assembly, go to an item's detail page and add components in the BOM tab.</p>
            }
          </div>
        } @else {
          <p-table
            [value]="filteredAssemblies()"
            [paginator]="true"
            [rows]="20"
            [rowsPerPageOptions]="[10, 20, 50]"
            [showCurrentPageReport]="true"
            currentPageReportTemplate="Showing {first} to {last} of {totalRecords} assemblies"
            styleClass="p-datatable-sm p-datatable-striped"
            [globalFilterFields]="['name', 'sku', 'description']"
          >
            <ng-template pTemplate="header">
              <tr>
                <th pSortableColumn="sku" style="width: 150px">SKU <p-sortIcon field="sku" /></th>
                <th pSortableColumn="name">Name <p-sortIcon field="name" /></th>
                <th pSortableColumn="componentCount" style="width: 120px">Components <p-sortIcon field="componentCount" /></th>
                <th pSortableColumn="totalQuantity" style="width: 120px">In Stock <p-sortIcon field="totalQuantity" /></th>
                <th pSortableColumn="status" style="width: 120px">Status <p-sortIcon field="status" /></th>
                <th style="width: 100px">Actions</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-item>
              <tr>
                <td>
                  <span class="sku-badge">{{ item.sku }}</span>
                </td>
                <td>
                  <div class="item-name">
                    {{ item.name }}
                    @if (item.description) {
                      <small class="text-muted d-block">{{ item.description | slice:0:50 }}{{ item.description.length > 50 ? '...' : '' }}</small>
                    }
                  </div>
                </td>
                <td>
                  <span class="component-count">
                    <i class="pi pi-box mr-1"></i>
                    {{ item.componentCount || 0 }}
                  </span>
                </td>
                <td>
                  <span [class]="getQuantityClass(item.totalQuantity)">
                    {{ item.totalQuantity | number }}
                  </span>
                </td>
                <td>
                  <p-tag
                    [value]="getStatusLabel(item.status)"
                    [severity]="getStatusSeverity(item.status)"
                  />
                </td>
                <td>
                  <button
                    pButton
                    icon="pi pi-eye"
                    class="p-button-text p-button-sm"
                    pTooltip="View BOM"
                    tooltipPosition="left"
                    (click)="viewBom(item)"
                  ></button>
                </td>
              </tr>
            </ng-template>
          </p-table>
        }
      </p-card>
    </div>

    <p-toast />
  `,
  styles: [`
    .bom-list-container {
      padding: 1.5rem;
    }

    .page-header {
      margin-bottom: 1.5rem;

      h1 {
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--text-color);
        margin: 0 0 0.5rem 0;
        display: flex;
        align-items: center;

        i {
          color: var(--primary-color);
        }
      }

      .text-muted {
        color: var(--text-color-secondary);
        margin: 0;
      }
    }

    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .search-box {
      min-width: 300px;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 4rem 2rem;
      gap: 1rem;
      color: var(--text-color-secondary);
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 4rem 2rem;
      text-align: center;

      .empty-icon {
        font-size: 4rem;
        color: var(--text-color-secondary);
        opacity: 0.5;
        margin-bottom: 1rem;
      }

      h3 {
        margin: 0 0 0.5rem 0;
        color: var(--text-color);
      }

      p {
        margin: 0;
        color: var(--text-color-secondary);
      }

      .hint {
        margin-top: 1rem;
        font-size: 0.875rem;
      }
    }

    .sku-badge {
      font-family: var(--font-mono);
      font-size: 0.875rem;
      background: var(--surface-100);
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
    }

    .item-name {
      small {
        font-size: 0.8rem;
      }
    }

    .component-count {
      display: inline-flex;
      align-items: center;
      color: var(--primary-color);
      font-weight: 500;
    }

    .quantity-low {
      color: var(--orange-500);
      font-weight: 500;
    }

    .quantity-out {
      color: var(--red-500);
      font-weight: 500;
    }

    .quantity-ok {
      color: var(--green-600);
    }
  `],
})
export class BomListComponent implements OnInit {
  // State
  assemblies = signal<IAssemblyItem[]>([]);
  isLoading = signal(true);
  searchTerm = '';

  // Computed filtered list
  filteredAssemblies = computed(() => {
    const items = this.assemblies();
    if (!this.searchTerm.trim()) {
      return items;
    }
    const term = this.searchTerm.toLowerCase();
    return items.filter(
      item =>
        item.name.toLowerCase().includes(term) ||
        item.sku.toLowerCase().includes(term) ||
        (item.description?.toLowerCase().includes(term) ?? false)
    );
  });

  constructor(
    private bomService: BomService,
    private inventoryService: InventoryService,
    private messageService: MessageService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadAssemblies();
  }

  async loadAssemblies(): Promise<void> {
    this.isLoading.set(true);
    try {
      // Get all inventory items first
      const itemsResult = await this.inventoryService.getItems(1, 1000).toPromise();
      const allItems = itemsResult?.items ?? [];

      // For each item, check if it has a BOM
      const assembliesWithBom: IAssemblyItem[] = [];
      
      for (const item of allItems) {
        if (!item.id) continue;
        
        try {
          const components = await this.bomService.getItemBom(item.id).toPromise();
          
          if (components && components.length > 0) {
            assembliesWithBom.push({
              ...item,
              componentCount: components.length,
            });
          }
        } catch {
          // Item has no BOM, skip it
        }
      }

      this.assemblies.set(assembliesWithBom);
    } catch (error) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load assemblies',
      });
    } finally {
      this.isLoading.set(false);
    }
  }

  onSearch(): void {
    // The computed signal handles the filtering
  }

  viewBom(item: IAssemblyItem): void {
    this.router.navigate(['/inventory', item.id], { queryParams: { tab: 'bom' } });
  }

  getQuantityClass(quantity: number): string {
    if (quantity <= 0) return 'quantity-out';
    if (quantity < 10) return 'quantity-low';
    return 'quantity-ok';
  }

  getStatusLabel(status: InventoryStatus): string {
    const labels: Record<InventoryStatus, string> = {
      [InventoryStatus.IN_STOCK]: 'In Stock',
      [InventoryStatus.LOW_STOCK]: 'Low Stock',
      [InventoryStatus.OUT_OF_STOCK]: 'Out of Stock',
      [InventoryStatus.ON_ORDER]: 'On Order',
      [InventoryStatus.DISCONTINUED]: 'Discontinued',
    };
    return labels[status] || status;
  }

  getStatusSeverity(status: InventoryStatus): 'success' | 'warning' | 'danger' | 'info' | 'secondary' {
    const severities: Record<InventoryStatus, 'success' | 'warning' | 'danger' | 'info' | 'secondary'> = {
      [InventoryStatus.IN_STOCK]: 'success',
      [InventoryStatus.LOW_STOCK]: 'warning',
      [InventoryStatus.OUT_OF_STOCK]: 'danger',
      [InventoryStatus.ON_ORDER]: 'info',
      [InventoryStatus.DISCONTINUED]: 'secondary',
    };
    return severities[status] || 'secondary';
  }
}
