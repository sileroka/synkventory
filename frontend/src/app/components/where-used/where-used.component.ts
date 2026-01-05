import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

// PrimeNG Modules
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';

import { BomService } from '../../services/bom.service';
import { IWhereUsedEntry } from '../../models/bill-of-material.model';

@Component({
  selector: 'app-where-used',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TableModule,
    ButtonModule,
    TagModule,
    TooltipModule,
  ],
  template: `
    <div class="where-used-container">
      <div class="where-used-header mb-3">
        <h4 class="m-0 text-600">Used In Assemblies</h4>
        <p class="text-500 text-sm mt-1 mb-0">Assemblies that use this item as a component</p>
      </div>

      <p-table
        [value]="whereUsed()"
        [loading]="isLoading()"
        styleClass="p-datatable-sm"
      >
        <ng-template pTemplate="header">
          <tr>
            <th style="width: 50px">Image</th>
            <th>Assembly</th>
            <th style="width: 80px">SKU</th>
            <th style="width: 100px">Qty Needed</th>
            <th style="width: 80px">In Stock</th>
            <th style="width: 80px">Actions</th>
          </tr>
        </ng-template>

        <ng-template pTemplate="body" let-entry>
          <tr>
            <td>
              <img
                *ngIf="entry.parentItem?.imageUrl"
                [src]="entry.parentItem.imageUrl"
                [alt]="entry.parentItem?.name"
                class="border-round"
                style="width: 36px; height: 36px; object-fit: cover;"
              />
              <span
                *ngIf="!entry.parentItem?.imageUrl"
                class="flex align-items-center justify-content-center border-round surface-200"
                style="width: 36px; height: 36px;"
              >
                <i class="pi pi-image text-400 text-sm"></i>
              </span>
            </td>
            <td>
              <div class="font-medium">{{ entry.parentItem?.name }}</div>
            </td>
            <td class="text-500">{{ entry.parentItem?.sku }}</td>
            <td class="font-semibold">{{ entry.quantityRequired }}</td>
            <td>
              <span
                [class.text-green-500]="(entry.parentItem?.quantity ?? 0) > 0"
                [class.text-red-500]="(entry.parentItem?.quantity ?? 0) === 0"
              >
                {{ entry.parentItem?.quantity ?? 0 }}
              </span>
            </td>
            <td>
              <p-button
                icon="pi pi-eye"
                [rounded]="true"
                [text]="true"
                severity="secondary"
                [routerLink]="['/inventory', entry.parentItemId]"
                pTooltip="View Assembly"
                tooltipPosition="left"
              />
            </td>
          </tr>
        </ng-template>

        <ng-template pTemplate="emptymessage">
          <tr>
            <td colspan="6" class="text-center p-4">
              <div class="text-500">
                <i class="pi pi-check-circle text-green-500 text-2xl mb-2 block"></i>
                <p class="m-0">This item is not used in any assemblies</p>
              </div>
            </td>
          </tr>
        </ng-template>
      </p-table>
    </div>
  `,
  styles: [`
    .where-used-container {
      padding: 0;
    }

    :host ::ng-deep {
      .p-datatable {
        .p-datatable-thead > tr > th {
          background: var(--surface-50);
          font-weight: 600;
          color: var(--text-color-secondary);
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          padding: 0.5rem 0.75rem;
        }
        
        .p-datatable-tbody > tr > td {
          padding: 0.5rem 0.75rem;
        }
      }
    }
  `]
})
export class WhereUsedComponent implements OnInit {
  @Input() itemId!: string;

  whereUsed = signal<IWhereUsedEntry[]>([]);
  isLoading = signal(false);

  constructor(private bomService: BomService) {}

  ngOnInit(): void {
    this.loadWhereUsed();
  }

  loadWhereUsed(): void {
    if (!this.itemId) return;

    this.isLoading.set(true);
    
    this.bomService.getWhereUsed(this.itemId).subscribe({
      next: (entries) => {
        this.whereUsed.set(entries);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error loading where-used:', error);
        this.isLoading.set(false);
      },
    });
  }
}
