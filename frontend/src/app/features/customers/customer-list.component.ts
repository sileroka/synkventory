import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { ToastModule } from 'primeng/toast';
import { MessageService, ConfirmationService } from 'primeng/api';

import { CustomerService } from '../../services/customer.service';
import { ICustomer, ICustomerCreate, ICustomerUpdate } from '../../models/customer.model';

@Component({
  selector: 'app-customer-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DialogModule,
    ToastModule,
    ConfirmDialogModule,
    TooltipModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './customer-list.component.html',
})
export class CustomerListComponent implements OnInit {
  customers = signal<ICustomer[]>([]);
  isLoading = signal<boolean>(true);
  search = '';
  page = 1;
  pageSize = 25;
  total = 0;

  // Create/Edit dialog
  showDialog = signal<boolean>(false);
  editingCustomer: ICustomer | null = null;
  form: ICustomerCreate | ICustomerUpdate = { name: '' };

  constructor(
    private customerService: CustomerService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit(): void {
    this.loadCustomers();
  }

  loadCustomers(): void {
    this.isLoading.set(true);
    this.customerService.getCustomers(this.page, this.pageSize, this.search).subscribe({
      next: (resp) => {
        this.customers.set(resp.items);
        this.total = resp.total;
        this.isLoading.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load customers' });
        this.isLoading.set(false);
      },
    });
  }

  onSearchChange(): void {
    this.page = 1;
    this.loadCustomers();
  }

  openCreate(): void {
    this.editingCustomer = null;
    this.form = { name: '' };
    this.showDialog.set(true);
  }

  openEdit(customer: ICustomer): void {
    this.editingCustomer = customer;
    this.form = {
      name: customer.name,
      email: customer.email || undefined,
      phone: customer.phone || undefined,
      shippingAddress: customer.shippingAddress || undefined,
      billingAddress: customer.billingAddress || undefined,
      notes: customer.notes || undefined,
    };
    this.showDialog.set(true);
  }

  save(): void {
    if (!this.form.name || this.form.name.trim().length === 0) {
      this.messageService.add({ severity: 'warn', summary: 'Validation', detail: 'Name is required' });
      return;
    }

    if (this.editingCustomer) {
      this.customerService.update(this.editingCustomer.id, this.form as ICustomerUpdate).subscribe({
        next: (customer) => {
          this.messageService.add({ severity: 'success', summary: 'Updated', detail: 'Customer updated' });
          this.showDialog.set(false);
          this.loadCustomers();
        },
        error: (err) => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to update customer' });
        },
      });
    } else {
      this.customerService.create(this.form as ICustomerCreate).subscribe({
        next: (customer) => {
          this.messageService.add({ severity: 'success', summary: 'Created', detail: 'Customer created' });
          this.showDialog.set(false);
          this.loadCustomers();
        },
        error: (err) => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to create customer' });
        },
      });
    }
  }

  deactivateOrDelete(customer: ICustomer): void {
    this.confirmationService.confirm({
      message: 'Deactivate or delete this customer? If referenced by sales orders, it will be deactivated.',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.customerService.delete(customer.id).subscribe({
          next: (resp) => {
            this.messageService.add({ severity: 'success', summary: 'Success', detail: resp.message || 'Customer updated' });
            this.loadCustomers();
          },
          error: (err) => {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to update customer' });
          },
        });
      },
    });
  }
}
