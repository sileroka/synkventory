import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';

import { SalesOrderService } from '../../services/sales-order.service';
import { ISalesOrderDetail, ISalesOrderLineItem, SalesOrderStatus, IShipItemsRequest } from '../../models/sales-order.model';

@Component({
  selector: 'app-sales-order-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    ToastModule,
    ConfirmDialogModule,
    TooltipModule,
  ],
  providers: [MessageService],
  templateUrl: './sales-order-detail.component.html'
})
export class SalesOrderDetailComponent implements OnInit {
  order = signal<ISalesOrderDetail | null>(null);
  isLoading = signal(false);

  constructor(
    private readonly route: ActivatedRoute,
    private readonly salesOrderService: SalesOrderService,
    private readonly messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadOrder();
  }

  async loadOrder() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.isLoading.set(true);
    try {
      const o = await this.salesOrderService.get(id);
      this.order.set(o);
    } finally {
      this.isLoading.set(false);
    }
  }

  get remainingItems(): Array<{ lineItemId: string; quantity: number }> {
    const o = this.order();
    if (!o) return [];
    return o.lineItems
      .map(li => ({ lineItemId: li.id, quantity: Math.max(li.quantityOrdered - li.quantityShipped, 0) }))
      .filter(x => x.quantity > 0);
  }

  canConfirm(): boolean {
    const o = this.order();
    return !!o && o.status === SalesOrderStatus.DRAFT;
  }

  canCancel(): boolean {
    const o = this.order();
    return !!o && (o.status === SalesOrderStatus.DRAFT || o.status === SalesOrderStatus.CONFIRMED);
  }

  canShip(): boolean {
    const o = this.order();
    return !!o && o.status === SalesOrderStatus.CONFIRMED && this.remainingItems.length > 0;
  }

  async confirm() {
    const o = this.order();
    if (!o) return;
    try {
      const updated = await this.salesOrderService.changeStatus(o.id, SalesOrderStatus.CONFIRMED);
      this.order.set(updated);
      this.toast('success', 'Order confirmed');
    } catch {
      this.toast('error', 'Confirm failed');
    }
  }

  async cancel() {
    const o = this.order();
    if (!o) return;
    try {
      const updated = await this.salesOrderService.changeStatus(o.id, SalesOrderStatus.CANCELLED);
      this.order.set(updated);
      this.toast('success', 'Order cancelled');
    } catch {
      this.toast('error', 'Cancel failed');
    }
  }

  async shipRemaining() {
    const o = this.order();
    if (!o) return;
    const items = this.remainingItems;
    if (items.length === 0) {
      this.toast('info', 'Nothing to ship');
      return;
    }
    const payload: IShipItemsRequest = { items };
    try {
      const updated = await this.salesOrderService.ship(o.id, payload);
      this.order.set(updated);
      this.toast('success', 'Shipment recorded');
    } catch {
      this.toast('error', 'Ship failed');
    }
  }

  private toast(severity: 'success' | 'info' | 'warn' | 'error', summary: string) {
    this.messageService.add({ severity, summary });
  }
}
