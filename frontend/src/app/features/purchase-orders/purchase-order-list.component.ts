import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

// PrimeNG Modules
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { CardModule } from 'primeng/card';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { CalendarModule } from 'primeng/calendar';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { AutoCompleteModule, AutoCompleteCompleteEvent } from 'primeng/autocomplete';
import { CheckboxModule } from 'primeng/checkbox';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ChipModule } from 'primeng/chip';
import { MessageService, ConfirmationService } from 'primeng/api';

import { PurchaseOrderService, IPurchaseOrderFilters } from '../../services/purchase-order.service';
import { InventoryService } from '../../services/inventory.service';
import { LocationService } from '../locations/services/location.service';
import { SupplierService } from '../../services/supplier.service';
import { ISupplier } from '../../models/supplier.model';
import {
  IPurchaseOrderListItem,
  IPurchaseOrder,
  IPurchaseOrderCreate,
  IPurchaseOrderStats,
  IPurchaseOrderLineItemCreate,
  ILowStockItem,
  ILowStockSuggestion,
  PurchaseOrderStatus,
  PurchaseOrderPriority,
  PurchaseOrderHelpers,
} from '../../models/purchase-order.model';
import { IInventoryItem } from '../../models/inventory-item.model';
import { ILocation } from '../locations/models/location.model';

@Component({
  selector: 'app-purchase-order-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    TooltipModule,
    TagModule,
    CardModule,
    ProgressSpinnerModule,
    ToastModule,
    DialogModule,
    InputNumberModule,
    CalendarModule,
    InputTextareaModule,
    AutoCompleteModule,
    CheckboxModule,
    ConfirmDialogModule,
    ChipModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './purchase-order-list.component.html',
  styleUrls: ['./purchase-order-list.component.scss'],
})
export class PurchaseOrderListComponent implements OnInit {
  // State
  purchaseOrders = signal<IPurchaseOrderListItem[]>([]);
  stats = signal<IPurchaseOrderStats | null>(null);
  isLoading = signal(true);

  // Pagination
  page = 1;
  pageSize = 25;
  totalRecords = 0;

  // Filters
  statusFilter: PurchaseOrderStatus | null = null;
  priorityFilter: PurchaseOrderPriority | null = null;
  includeReceived = false;
  supplierFilterId: string | null = null;
  showCreateSupplierDialog = signal(false);
  supplierForm: { name: string; contactName?: string; email?: string; phone?: string } = { name: '' };

  statusOptions = [
    { label: 'All Active', value: null },
    { label: 'Draft', value: PurchaseOrderStatus.DRAFT },
    { label: 'Pending Approval', value: PurchaseOrderStatus.PENDING_APPROVAL },
    { label: 'Approved', value: PurchaseOrderStatus.APPROVED },
    { label: 'Ordered', value: PurchaseOrderStatus.ORDERED },
    { label: 'Partially Received', value: PurchaseOrderStatus.PARTIALLY_RECEIVED },
    { label: 'Received', value: PurchaseOrderStatus.RECEIVED },
    { label: 'Cancelled', value: PurchaseOrderStatus.CANCELLED },
  ];

  priorityOptions = [
    { label: 'All Priorities', value: null },
    { label: 'Low', value: PurchaseOrderPriority.LOW },
    { label: 'Normal', value: PurchaseOrderPriority.NORMAL },
    { label: 'High', value: PurchaseOrderPriority.HIGH },
    { label: 'Urgent', value: PurchaseOrderPriority.URGENT },
  ];

  // Create dialog
  showCreateDialog = signal(false);
  showLowStockDialog = signal(false);

  // Create form
  newPO: IPurchaseOrderCreate = this.getEmptyPO();
  newLineItems: IPurchaseOrderLineItemCreate[] = [];

  // Low stock
  lowStockSuggestion = signal<ILowStockSuggestion | null>(null);
  selectedLowStockItems: ILowStockItem[] = [];
  lowStockSupplierName = '';
  // Forecast params for low-stock suggestions
  leadTimeDays = 14;
  safetyStock = 0;

  // Item autocomplete
  filteredItems: IInventoryItem[] = [];
  selectedItem: IInventoryItem | null = null;
  newLineQuantity = 1;
  newLinePrice = 0;

  // Locations
  locations = signal<ILocation[]>([]);

  // Suppliers
  suppliers = signal<ISupplier[]>([]);

  // Helpers
  helpers = PurchaseOrderHelpers;

  constructor(
    private purchaseOrderService: PurchaseOrderService,
    private inventoryService: InventoryService,
    private locationService: LocationService,
    private supplierService: SupplierService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadPurchaseOrders();
    this.loadStats();
    this.loadLocations();
    this.loadSuppliers();
  }

  loadPurchaseOrders(): void {
    this.isLoading.set(true);

    const filters: IPurchaseOrderFilters = {
      page: this.page,
      pageSize: this.pageSize,
      status: this.statusFilter || undefined,
      priority: this.priorityFilter || undefined,
      includeReceived: this.includeReceived,
      supplierId: this.supplierFilterId || undefined,
    };

    this.purchaseOrderService.getPurchaseOrders(filters).subscribe({
      next: (response) => {
        this.purchaseOrders.set(response.items);
        this.totalRecords = response.total;
        this.isLoading.set(false);
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load purchase orders',
        });
        this.isLoading.set(false);
      },
    });
  }

  loadStats(): void {
    this.purchaseOrderService.getStats().subscribe({
      next: (stats) => this.stats.set(stats),
      error: () => { },
    });
  }

  loadLocations(): void {
    this.locationService.getLocations().subscribe({
      next: (response) => this.locations.set(response.items || response),
      error: () => { },
    });
  }

  loadSuppliers(): void {
    // Backend enforces page_size <= 100; request max 100
    this.supplierService.getSuppliers(1, 100).subscribe({
      next: (resp: { items: ISupplier[]; total: number; page: number; pageSize: number }) => this.suppliers.set(resp.items),
      error: () => { },
    });
  }

  onPageChange(event: any): void {
    // PrimeNG onPage emits { first, rows, page }
    if (event && typeof event.page === 'number') {
      this.page = event.page + 1; // event.page is 0-based
    } else if (event && typeof event.first === 'number' && typeof event.rows === 'number') {
      this.page = Math.floor(event.first / event.rows) + 1;
    }
    if (event && typeof event.rows === 'number') {
      this.pageSize = event.rows;
    }
    this.loadPurchaseOrders();
  }

  onFilterChange(): void {
    this.page = 1;
    this.loadPurchaseOrders();
  }

  viewPurchaseOrder(po: IPurchaseOrderListItem): void {
    this.router.navigate(['/purchase-orders', po.id]);
  }

  // ==========================================================================
  // CREATE DIALOG
  // ==========================================================================

  openCreateDialog(): void {
    this.newPO = this.getEmptyPO();
    this.newLineItems = [];
    this.selectedItem = null;
    this.newLineQuantity = 1;
    this.newLinePrice = 0;
    this.showCreateDialog.set(true);
  }

  getEmptyPO(): IPurchaseOrderCreate {
    return {
      supplierId: undefined,
      supplierName: '',
      supplierContact: '',
      supplierEmail: '',
      supplierPhone: '',
      priority: PurchaseOrderPriority.NORMAL,
      expectedDate: undefined,
      receivingLocationId: undefined,
      notes: '',
    };
  }

  onSupplierSelected(supplierId: string | null): void {
  const supplier = this.suppliers().find((s: ISupplier) => s.id === supplierId);
    if (supplier) {
      this.newPO.supplierId = supplier.id;
      this.newPO.supplierName = supplier.name;
      this.newPO.supplierContact = supplier.contactName || '';
      this.newPO.supplierEmail = supplier.email || '';
      this.newPO.supplierPhone = supplier.phone || '';
    } else {
      this.newPO.supplierId = undefined;
    }
  }

  openCreateSupplier(): void {
    this.supplierForm = { name: '', contactName: '', email: '', phone: '' };
    this.showCreateSupplierDialog.set(true);
  }

  saveSupplierInline(): void {
    const { name, contactName, email, phone } = this.supplierForm;
    if (!name || name.trim().length === 0) {
      this.messageService.add({ severity: 'warn', summary: 'Validation', detail: 'Supplier name is required' });
      return;
    }
    // Basic validations
    if (email && !/^\S+@\S+\.\S+$/.test(email)) {
      this.messageService.add({ severity: 'warn', summary: 'Validation', detail: 'Please enter a valid email address' });
      return;
    }
    if (phone && !/^[+()\-\s0-9]{7,20}$/.test(phone)) {
      this.messageService.add({ severity: 'warn', summary: 'Validation', detail: 'Please enter a valid phone number' });
      return;
    }
    this.supplierService.create({ name, contactName, email, phone }).subscribe({
  next: (supplier: ISupplier) => {
        this.messageService.add({ severity: 'success', summary: 'Created', detail: 'Supplier created' });
        this.showCreateSupplierDialog.set(false);
        // Refresh suppliers and select the newly created one
        this.loadSuppliers();
        this.onSupplierSelected(supplier.id);
        this.newPO.supplierId = supplier.id;
      },
  error: (err: any) => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to create supplier' });
      },
    });
  }

  clearFilters(): void {
    this.statusFilter = null;
    this.priorityFilter = null;
    this.includeReceived = false;
    this.supplierFilterId = null;
    this.page = 1;
    this.loadPurchaseOrders();
  }

  onSupplierFilterChange(supplierId: string | null): void {
    this.supplierFilterId = supplierId;
    this.page = 1;
    this.loadPurchaseOrders();
  const supplier = this.suppliers().find((s: ISupplier) => s.id === supplierId);
    if (supplierId && supplier) {
      this.messageService.add({ severity: 'info', summary: 'Filtered', detail: `Filtered by supplier: ${supplier.name}` });
    } else {
      this.messageService.add({ severity: 'info', summary: 'Filter cleared', detail: 'Supplier filter removed' });
    }
  }

  searchItems(event: AutoCompleteCompleteEvent): void {
    this.inventoryService.getItems(1, 20, { search: event.query }).subscribe({
      next: (response: { items: IInventoryItem[] }) => {
        this.filteredItems = response.items;
      },
    });
  }

  addLineItem(): void {
    if (!this.selectedItem) return;

    // Check if already added
    if (this.newLineItems.some(li => li.itemId === this.selectedItem!.id)) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Already Added',
        detail: 'This item is already in the order',
      });
      return;
    }

    this.newLineItems.push({
      itemId: this.selectedItem.id!,
      quantityOrdered: this.newLineQuantity,
      unitPrice: this.newLinePrice || this.selectedItem.unitPrice,
    });

    this.selectedItem = null;
    this.newLineQuantity = 1;
    this.newLinePrice = 0;
  }

  removeLineItem(index: number): void {
    this.newLineItems.splice(index, 1);
  }

  getLineItemTotal(): number {
    return this.newLineItems.reduce((sum, li) => sum + li.quantityOrdered * li.unitPrice, 0);
  }

  getItemName(itemId: string): string {
    const item = this.filteredItems.find(i => i.id === itemId);
    return item ? `${item.sku} - ${item.name}` : itemId;
  }

  createPurchaseOrder(): void {
    if (this.newLineItems.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Items',
        detail: 'Please add at least one item to the order',
      });
      return;
    }

    const createData: IPurchaseOrderCreate = {
      ...this.newPO,
      lineItems: this.newLineItems,
    };

    this.purchaseOrderService.createPurchaseOrder(createData).subscribe({
      next: (po: IPurchaseOrder) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Created',
          detail: `Purchase order ${po.poNumber} created`,
        });
        this.showCreateDialog.set(false);
        this.loadPurchaseOrders();
        this.loadStats();
        this.router.navigate(['/purchase-orders', po.id]);
      },
  error: (error: any) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.error?.detail || 'Failed to create purchase order',
        });
      },
    });
  }

  // ==========================================================================
  // LOW STOCK DIALOG
  // ==========================================================================

  openLowStockDialog(): void {
    this.loadLowStockItems();
    this.selectedLowStockItems = [];
    this.lowStockSupplierName = '';
    this.showLowStockDialog.set(true);
  }

  loadLowStockItems(): void {
    this.purchaseOrderService.getLowStockSuggestions(100, this.leadTimeDays, this.safetyStock).subscribe({
      next: (suggestion: ILowStockSuggestion) => this.lowStockSuggestion.set(suggestion),
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load low stock items',
        });
      },
    });
  }

  selectAllLowStock(): void {
    const suggestion = this.lowStockSuggestion();
    if (suggestion) {
      this.selectedLowStockItems = [...suggestion.items];
    }
  }

  deselectAllLowStock(): void {
    this.selectedLowStockItems = [];
  }

  getSelectedLowStockTotal(): number {
    return this.selectedLowStockItems.reduce(
      (sum, item) => sum + item.suggestedQuantity * item.unitPrice,
      0
    );
  }

  createPOFromLowStock(): void {
    if (this.selectedLowStockItems.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Items Selected',
        detail: 'Please select at least one item',
      });
      return;
    }

    const itemIds = this.selectedLowStockItems.map(item => item.id);

    this.purchaseOrderService.createFromLowStock(itemIds, this.lowStockSupplierName || undefined).subscribe({
      next: (po: IPurchaseOrder) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Created',
          detail: `Purchase order ${po.poNumber} created with ${this.selectedLowStockItems.length} items`,
        });
        this.showLowStockDialog.set(false);
        this.loadPurchaseOrders();
        this.loadStats();
        this.router.navigate(['/purchase-orders', po.id]);
      },
  error: (error: any) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.error?.detail || 'Failed to create purchase order',
        });
      },
    });
  }

  // ==========================================================================
  // HELPERS
  // ==========================================================================

  getStatusLabel(status: string): string {
    return PurchaseOrderHelpers.getStatusLabel(status);
  }

  getStatusSeverity(status: string): 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast' {
    const severity = PurchaseOrderHelpers.getStatusSeverity(status);
    return severity === 'warn' ? 'warning' : severity;
  }

  getPriorityLabel(priority: string): string {
    return PurchaseOrderHelpers.getPriorityLabel(priority);
  }

  getPrioritySeverity(priority: string): 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast' {
    const severity = PurchaseOrderHelpers.getPrioritySeverity(priority);
    return severity === 'warn' ? 'warning' : severity;
  }

  getSupplierTooltip(po: IPurchaseOrderListItem): string {
    const s = (po as any).supplier as ISupplier | undefined;
    if (!s) return '';
    const parts: string[] = [];
    if (s.contactName) parts.push(`Contact: ${s.contactName}`);
    if (s.email) parts.push(`Email: ${s.email}`);
    if (s.phone) parts.push(`Phone: ${s.phone}`);
    return parts.join(' | ');
  }
}
