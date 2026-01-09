import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

// PrimeNG
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TooltipModule } from 'primeng/tooltip';
import { TimelineModule } from 'primeng/timeline';
import { ConfirmationService, MessageService } from 'primeng/api';

import { PurchaseOrderService } from '../../services/purchase-order.service';
import {
  IPurchaseOrder,
  IPurchaseOrderLineItem,
  IPurchaseOrderLineItemWithItem,
  PurchaseOrderStatus,
  PurchaseOrderPriority,
  PurchaseOrderHelpers,
  IReceiveLineItem,
} from '../../models/purchase-order.model';
import { LocationService } from '../locations/services/location.service';
import { ILocation } from '../locations/models/location.model';

interface TimelineEvent {
  status: string;
  date: Date | null;
  icon: string;
  color: string;
  label: string;
  isActive: boolean;
  isComplete: boolean;
}

@Component({
  selector: 'app-purchase-order-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    CardModule,
    ButtonModule,
    TagModule,
    TableModule,
    DialogModule,
    InputTextModule,
    InputNumberModule,
    InputTextareaModule,
    CalendarModule,
    DropdownModule,
    ToastModule,
    ConfirmDialogModule,
    ProgressSpinnerModule,
    TooltipModule,
    TimelineModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './purchase-order-detail.component.html',
  styleUrl: './purchase-order-detail.component.scss',
})
export class PurchaseOrderDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private purchaseOrderService = inject(PurchaseOrderService);
  private locationService = inject(LocationService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  purchaseOrder = signal<IPurchaseOrder | null>(null);
  isLoading = signal(true);
  locations = signal<ILocation[]>([]);

  // Dialogs
  showReceiveDialog = signal(false);
  showEditDialog = signal(false);

  // Receive form
  receiveItems: IReceiveLineItem[] = [];

  // Edit form
  editData = {
    supplierName: '',
    supplierContact: '',
    supplierEmail: '',
    supplierPhone: '',
    expectedDate: null as Date | null,
    receivingLocationId: '',
    notes: '',
  };

  // Computed properties
  canEdit = computed(() => {
    const po = this.purchaseOrder();
    return po && po.status === PurchaseOrderStatus.DRAFT;
  });

  canSubmit = computed(() => {
    const po = this.purchaseOrder();
    return po && po.status === PurchaseOrderStatus.DRAFT && po.lineItems.length > 0;
  });

  canApprove = computed(() => {
    const po = this.purchaseOrder();
    return po && po.status === PurchaseOrderStatus.PENDING_APPROVAL;
  });

  canMarkOrdered = computed(() => {
    const po = this.purchaseOrder();
    return po && po.status === PurchaseOrderStatus.APPROVED;
  });

  canReceive = computed(() => {
    const po = this.purchaseOrder();
    return (
      po &&
      (po.status === PurchaseOrderStatus.ORDERED || po.status === PurchaseOrderStatus.PARTIALLY_RECEIVED)
    );
  });

  canCancel = computed(() => {
    const po = this.purchaseOrder();
    return (
      po &&
      po.status !== PurchaseOrderStatus.RECEIVED &&
      po.status !== PurchaseOrderStatus.CANCELLED
    );
  });

  statusTimeline = computed((): TimelineEvent[] => {
    const po = this.purchaseOrder();
    if (!po) return [];

    const statusOrder = [
      { status: PurchaseOrderStatus.DRAFT, label: 'Draft', icon: 'pi pi-file', color: '#94a3b8' },
      { status: PurchaseOrderStatus.PENDING_APPROVAL, label: 'Pending', icon: 'pi pi-send', color: '#6366f1' },
      { status: PurchaseOrderStatus.APPROVED, label: 'Approved', icon: 'pi pi-check-circle', color: '#0d9488' },
      { status: PurchaseOrderStatus.ORDERED, label: 'Ordered', icon: 'pi pi-shopping-cart', color: '#f59e0b' },
      { status: PurchaseOrderStatus.RECEIVED, label: 'Received', icon: 'pi pi-inbox', color: '#10b981' },
    ];

    const currentIndex = statusOrder.findIndex((s) => s.status === po.status);
    const isCancelled = po.status === PurchaseOrderStatus.CANCELLED;
    const isPartial = po.status === PurchaseOrderStatus.PARTIALLY_RECEIVED;

    return statusOrder.map((s, i) => ({
      ...s,
      date: this.getStatusDate(po, s.status),
      isActive: isCancelled ? false : isPartial ? i <= 3 : i === currentIndex,
      isComplete: isCancelled ? false : isPartial ? i < 4 : i < currentIndex,
    }));
  });

  ngOnInit(): void {
    this.loadLocations();
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadPurchaseOrder(id);
    }
  }

  loadPurchaseOrder(id: string): void {
    this.isLoading.set(true);
    this.purchaseOrderService.getById(id).subscribe({
      next: (response) => {
        this.purchaseOrder.set(response.data);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load purchase order',
        });
        this.isLoading.set(false);
        this.router.navigate(['/purchase-orders']);
      },
    });
  }
  
  getSupplierTooltip(po: IPurchaseOrder): string {
    const parts: string[] = [];
    const supplier = po.supplier;
    const contact = supplier?.contactName || po.supplierContact;
    const email = supplier?.email || po.supplierEmail;
    const phone = supplier?.phone || po.supplierPhone;
    if (contact) parts.push(`Contact: ${contact}`);
    if (email) parts.push(`Email: ${email}`);
    if (phone) parts.push(`Phone: ${phone}`);
    return parts.join('\n');
  }

  loadLocations(): void {
    this.locationService.getLocations().subscribe({
      next: (response) => this.locations.set(response.items),
    });
  }

  private getStatusDate(po: IPurchaseOrder, status: PurchaseOrderStatus): Date | null {
    switch (status) {
      case PurchaseOrderStatus.DRAFT:
        return new Date(po.createdAt);
      case PurchaseOrderStatus.ORDERED:
        return po.orderDate ? new Date(po.orderDate) : null;
      case PurchaseOrderStatus.RECEIVED:
        return po.receivedDate ? new Date(po.receivedDate) : null;
      default:
        // We don't have separate timestamps for pending_approval and approved
        return null;
    }
  }

  getStatusSeverity(status: string): 'success' | 'secondary' | 'info' | 'warning' | 'danger' | 'contrast' {
    const severity = PurchaseOrderHelpers.getStatusSeverity(status);
    return severity === 'warn' ? 'warning' : severity;
  }

  getPrioritySeverity(priority: string): 'success' | 'secondary' | 'info' | 'warning' | 'danger' | 'contrast' {
    const severity = PurchaseOrderHelpers.getPrioritySeverity(priority);
    return severity === 'warn' ? 'warning' : severity;
  }

  getStatusLabel(status: string): string {
    return PurchaseOrderHelpers.getStatusLabel(status);
  }

  getPriorityLabel(priority: string): string {
    return PurchaseOrderHelpers.getPriorityLabel(priority);
  }

  // Actions
  goBack(): void {
    this.router.navigate(['/purchase-orders']);
  }

  submitForApproval(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to submit this purchase order for approval?',
      header: 'Submit for Approval',
      icon: 'pi pi-send',
      accept: () => {
        const po = this.purchaseOrder();
        if (!po) return;

        this.purchaseOrderService.submit(po.id).subscribe({
          next: (response) => {
            this.purchaseOrder.set(response.data);
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Purchase order submitted for approval',
            });
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to submit purchase order',
            });
          },
        });
      },
    });
  }

  approvePurchaseOrder(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to approve this purchase order?',
      header: 'Approve Purchase Order',
      icon: 'pi pi-check-circle',
      accept: () => {
        const po = this.purchaseOrder();
        if (!po) return;

        this.purchaseOrderService.approve(po.id).subscribe({
          next: (response) => {
            this.purchaseOrder.set(response.data);
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Purchase order approved',
            });
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to approve purchase order',
            });
          },
        });
      },
    });
  }

  markAsOrdered(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to mark this purchase order as ordered?',
      header: 'Mark as Ordered',
      icon: 'pi pi-shopping-cart',
      accept: () => {
        const po = this.purchaseOrder();
        if (!po) return;

        this.purchaseOrderService.order(po.id).subscribe({
          next: (response) => {
            this.purchaseOrder.set(response.data);
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Purchase order marked as ordered',
            });
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to update purchase order',
            });
          },
        });
      },
    });
  }

  openReceiveDialog(): void {
    const po = this.purchaseOrder();
    if (!po) return;

    this.receiveItems = po.lineItems
      .filter((item) => item.quantityOrdered > item.quantityReceived)
      .map((item) => ({
        lineItemId: item.id,
        quantityReceived: 0,
        notes: '',
        lots: []
      }));

    this.showReceiveDialog.set(true);
  }

  receiveLineItems(): void {
    const po = this.purchaseOrder();
    if (!po) return;

    const itemsToReceive = this.receiveItems.filter((item) => item.quantityReceived > 0);
    if (itemsToReceive.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Warning',
        detail: 'Please enter quantities to receive',
      });
      return;
    }

    this.purchaseOrderService.receive(po.id, itemsToReceive).subscribe({
      next: (response) => {
        this.purchaseOrder.set(response.data);
        this.showReceiveDialog.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Items received successfully',
        });
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to receive items',
        });
      },
    });
  }

  addLotToReceiveItem(itemIndex: number): void {
    const receiveItem = this.receiveItems[itemIndex];
    if (!receiveItem.lots) {
      receiveItem.lots = [];
    }
    receiveItem.lots.push({
      lotNumber: '',
      serialNumber: undefined,
      quantity: 1,
      expirationDate: undefined,
      manufactureDate: undefined,
    });
  }

  removeLotFromReceiveItem(itemIndex: number, lotIndex: number): void {
    const receiveItem = this.receiveItems[itemIndex];
    if (receiveItem.lots) {
      receiveItem.lots.splice(lotIndex, 1);
    }
  }

  // Helper methods for date handling in template
  getLotManufactureDate(itemIndex: number, lotIndex: number): Date | null {
    const lot = this.receiveItems[itemIndex].lots?.[lotIndex];
    return lot?.manufactureDate ? new Date(lot.manufactureDate) : null;
  }

  setLotManufactureDate(itemIndex: number, lotIndex: number, date: Date | null): void {
    const lot = this.receiveItems[itemIndex].lots?.[lotIndex];
    if (lot) {
      lot.manufactureDate = date ? this.formatDateToISO(date) : undefined;
    }
  }

  getLotExpirationDate(itemIndex: number, lotIndex: number): Date | null {
    const lot = this.receiveItems[itemIndex].lots?.[lotIndex];
    return lot?.expirationDate ? new Date(lot.expirationDate) : null;
  }

  setLotExpirationDate(itemIndex: number, lotIndex: number, date: Date | null): void {
    const lot = this.receiveItems[itemIndex].lots?.[lotIndex];
    if (lot) {
      lot.expirationDate = date ? this.formatDateToISO(date) : undefined;
    }
  }

  private formatDateToISO(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  // Track by function for lots
  trackByIndex(index: number): number {
    return index;
  }

  openEditDialog(): void {
    const po = this.purchaseOrder();
    if (!po) return;

    this.editData = {
      supplierName: po.supplierName || '',
      supplierContact: po.supplierContact || '',
      supplierEmail: po.supplierEmail || '',
      supplierPhone: po.supplierPhone || '',
      expectedDate: po.expectedDate ? new Date(po.expectedDate) : null,
      receivingLocationId: po.receivingLocationId || '',
      notes: po.notes || '',
    };

    this.showEditDialog.set(true);
  }

  savePurchaseOrder(): void {
    const po = this.purchaseOrder();
    if (!po) return;

    const updateData = {
      supplierName: this.editData.supplierName || undefined,
      supplierContact: this.editData.supplierContact || undefined,
      supplierEmail: this.editData.supplierEmail || undefined,
      supplierPhone: this.editData.supplierPhone || undefined,
      expectedDate: this.editData.expectedDate?.toISOString().split('T')[0],
      receivingLocationId: this.editData.receivingLocationId || undefined,
      notes: this.editData.notes || undefined,
    };

    this.purchaseOrderService.update(po.id, updateData).subscribe({
      next: (response) => {
        this.purchaseOrder.set(response.data);
        this.showEditDialog.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Purchase order updated',
        });
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to update purchase order',
        });
      },
    });
  }

  cancelPurchaseOrder(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to cancel this purchase order? This action cannot be undone.',
      header: 'Cancel Purchase Order',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        const po = this.purchaseOrder();
        if (!po) return;

        this.purchaseOrderService.cancel(po.id).subscribe({
          next: (response) => {
            this.purchaseOrder.set(response.data);
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Purchase order cancelled',
            });
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to cancel purchase order',
            });
          },
        });
      },
    });
  }

  deletePurchaseOrder(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete this purchase order? This action cannot be undone.',
      header: 'Delete Purchase Order',
      icon: 'pi pi-trash',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        const po = this.purchaseOrder();
        if (!po) return;

        this.purchaseOrderService.delete(po.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Purchase order deleted',
            });
            this.router.navigate(['/purchase-orders']);
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete purchase order',
            });
          },
        });
      },
    });
  }

  getLineItem(lineItemId: string): IPurchaseOrderLineItemWithItem | undefined {
    return this.purchaseOrder()?.lineItems.find((item) => item.id === lineItemId);
  }

  getRemainingQuantity(lineItemId: string): number {
    const lineItem = this.getLineItem(lineItemId);
    return lineItem ? lineItem.quantityOrdered - lineItem.quantityReceived : 0;
  }
}
