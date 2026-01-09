import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DialogModule } from 'primeng/dialog';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';

import { SalesOrderService } from '../../services/sales-order.service';
import { CustomerService } from '../../services/customer.service';
import { ISalesOrderListItem, SalesOrderStatus, ISalesOrderCreate } from '../../models/sales-order.model';
import { ICustomer } from '../../models/customer.model';
import { firstValueFrom } from 'rxjs';

@Component({
  selector: 'app-sales-order-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DialogModule,
    DropdownModule,
    ToastModule,
    ConfirmDialogModule,
    TooltipModule,
  ],
  providers: [MessageService],
  templateUrl: './sales-order-list.component.html'
})
export class SalesOrderListComponent implements OnInit {
  orders = signal<ISalesOrderListItem[]>([]);
  total = 0;
  page = 1;
  pageSize = 25;
  search = '';
  statusFilter?: SalesOrderStatus;
  isLoading = signal(false);

  // Create dialog
  showDialog = signal(false);
  customers = signal<ICustomer[]>([]);
  selectedCustomerId: string | null = null;
  notes = '';

  constructor(
    private readonly salesOrderService: SalesOrderService,
    private readonly customerService: CustomerService,
    private readonly messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadOrders();
    this.loadCustomers();
  }

  async loadOrders() {
    this.isLoading.set(true);
    try {
      const res = await this.salesOrderService.list({ page: this.page, pageSize: this.pageSize, search: this.search, status: this.statusFilter });
      this.orders.set(res.items);
      this.total = res.total;
    } finally {
      this.isLoading.set(false);
    }
  }

  async loadCustomers() {
    const res = await firstValueFrom(this.customerService.getCustomers(1, 100));
    this.customers.set(res.items);
  }

  onSearchChange() {
    this.page = 1;
    this.loadOrders();
  }

  openCreate() {
    this.selectedCustomerId = null;
    this.notes = '';
    this.showDialog.set(true);
  }

  async createOrder() {
    if (!this.selectedCustomerId) {
      this.toast('warn', 'Please select a customer');
      return;
    }
    const payload: ISalesOrderCreate = { customerId: this.selectedCustomerId, notes: this.notes };
    try {
      const order = await this.salesOrderService.create(payload);
      this.toast('success', `Created order ${order.orderNumber}`);
      this.showDialog.set(false);
      this.loadOrders();
    } catch (err) {
      this.toast('error', 'Create failed');
    }
  }

  private toast(severity: 'success' | 'info' | 'warn' | 'error', summary: string) {
    this.messageService.add({ severity, summary });
  }
}
