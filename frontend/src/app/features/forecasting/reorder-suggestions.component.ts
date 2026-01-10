import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { Router } from '@angular/router';

import { ForecastingService, IReorderSuggestion } from '../../services/forecasting.service';
import { PurchaseOrderService } from '../../services/purchase-order.service';

@Component({
  selector: 'app-reorder-suggestions',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    CardModule,
    TagModule,
    ProgressSpinnerModule,
    ToastModule,
  ],
  providers: [MessageService],
  templateUrl: './reorder-suggestions.component.html',
  styleUrls: ['./reorder-suggestions.component.scss'],
})
export class ReorderSuggestionsComponent implements OnInit {
  suggestions = signal<IReorderSuggestion[]>([]);
  isLoading = signal<boolean>(true);

  // Filters/controls
  leadTimeDays = 7;
  search = '';
  supplierName = '';
  selectedIds = signal<Set<string>>(new Set());

  filtered = computed(() => {
    const q = this.search.trim().toLowerCase();
    const items = this.suggestions();
    if (!q) return items;
    return items.filter(
      (s) => s.itemId.toLowerCase().includes(q) || (s.itemName || '').toLowerCase().includes(q)
    );
  });

  private router = inject(Router);
  constructor(
    private forecastingService: ForecastingService,
    private purchaseOrderService: PurchaseOrderService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadSuggestions();
  }

  loadSuggestions(): void {
    this.isLoading.set(true);
    this.forecastingService.getReorderSuggestions(this.leadTimeDays).subscribe({
      next: (data) => {
        this.suggestions.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load suggestions' });
        this.isLoading.set(false);
      },
    });
  }

  refresh(): void {
    this.loadSuggestions();
  }

  toggleSelection(itemId: string, checked: boolean): void {
    this.selectedIds.update((ids) => {
      const next = new Set(ids);
      if (checked) next.add(itemId); else next.delete(itemId);
      return next;
    });
  }

  createPurchaseOrder(): void {
    const ids = Array.from(this.selectedIds());
    if (ids.length === 0) {
      this.messageService.add({ severity: 'warn', summary: 'No Items', detail: 'Select one or more items.' });
      return;
    }
    this.isLoading.set(true);
    this.purchaseOrderService.createFromLowStock(ids, this.supplierName || undefined).subscribe({
      next: (po) => {
        this.isLoading.set(false);
        this.messageService.add({ severity: 'success', summary: 'Purchase Order Created', detail: po.poNumber });
        this.router.navigate(['/purchase-orders', po.id]);
      },
      error: () => {
        this.isLoading.set(false);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to create purchase order' });
      },
    });
  }
}
