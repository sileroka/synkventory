import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService, ConfirmationService } from 'primeng/api';

import { SupplierService } from '../../services/supplier.service';
import { ISupplier, ISupplierCreate, ISupplierUpdate } from '../../models/supplier.model';

@Component({
  selector: 'app-supplier-list',
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
  templateUrl: './supplier-list.component.html',
})
export class SupplierListComponent implements OnInit {
  suppliers = signal<ISupplier[]>([]);
  isLoading = signal<boolean>(true);
  search = '';
  page = 1;
  pageSize = 25;
  total = 0;

  // Create/Edit dialog
  showDialog = signal<boolean>(false);
  editingSupplier: ISupplier | null = null;
  form: ISupplierCreate | ISupplierUpdate = { name: '' };

  constructor(
    private supplierService: SupplierService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit(): void {
    this.loadSuppliers();
  }

  loadSuppliers(): void {
    this.isLoading.set(true);
    this.supplierService.getSuppliers(this.page, this.pageSize, this.search).subscribe({
      next: (resp) => {
        this.suppliers.set(resp.items);
        this.total = resp.total;
        this.isLoading.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load suppliers' });
        this.isLoading.set(false);
      },
    });
  }

  onSearchChange(): void {
    this.page = 1;
    this.loadSuppliers();
  }

  openCreate(): void {
    this.editingSupplier = null;
    this.form = { name: '' };
    this.showDialog.set(true);
  }

  openEdit(supplier: ISupplier): void {
    this.editingSupplier = supplier;
    this.form = {
      name: supplier.name,
      contactName: supplier.contactName,
      email: supplier.email,
      phone: supplier.phone,
      addressLine1: supplier.addressLine1,
      addressLine2: supplier.addressLine2,
      city: supplier.city,
      state: supplier.state,
      postalCode: supplier.postalCode,
      country: supplier.country,
      notes: supplier.notes,
    };
    this.showDialog.set(true);
  }

  save(): void {
    if (!this.form.name || this.form.name.trim().length === 0) {
      this.messageService.add({ severity: 'warn', summary: 'Validation', detail: 'Name is required' });
      return;
    }

    if (this.editingSupplier) {
      this.supplierService.update(this.editingSupplier.id, this.form as ISupplierUpdate).subscribe({
        next: (supplier) => {
          this.messageService.add({ severity: 'success', summary: 'Updated', detail: 'Supplier updated' });
          this.showDialog.set(false);
          this.loadSuppliers();
        },
        error: (err) => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to update supplier' });
        },
      });
    } else {
      this.supplierService.create(this.form as ISupplierCreate).subscribe({
        next: (supplier) => {
          this.messageService.add({ severity: 'success', summary: 'Created', detail: 'Supplier created' });
          this.showDialog.set(false);
          this.loadSuppliers();
        },
        error: (err) => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to create supplier' });
        },
      });
    }
  }

  deactivateOrDelete(supplier: ISupplier): void {
    this.confirmationService.confirm({
      message: 'Deactivate or delete this supplier? If referenced by POs, it will be deactivated.',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.supplierService.delete(supplier.id).subscribe({
          next: (resp) => {
            this.messageService.add({ severity: 'success', summary: 'Success', detail: resp.message });
            this.loadSuppliers();
          },
          error: (err) => {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to update supplier' });
          },
        });
      },
    });
  }

  getSupplierTooltip(supplier: ISupplier): string {
    const parts: string[] = [];
    if (supplier.contactName) parts.push(`Contact: ${supplier.contactName}`);
    if (supplier.email) parts.push(`Email: ${supplier.email}`);
    if (supplier.phone) parts.push(`Phone: ${supplier.phone}`);
    return parts.join(' | ');
  }
}
