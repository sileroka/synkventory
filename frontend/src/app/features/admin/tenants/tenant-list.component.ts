import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { AdminApiService, Tenant, TenantCreate } from '../../../core/services/admin-api.service';
import { AdminAuthService } from '../../../core/services/admin-auth.service';

@Component({
  selector: 'app-tenant-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    TagModule,
    ToastModule,
    TooltipModule,
    ConfirmDialogModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './tenant-list.component.html',
  styleUrl: './tenant-list.component.scss'
})
export class TenantListComponent implements OnInit {
  private adminApiService = inject(AdminApiService);
  private adminAuthService = inject(AdminAuthService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  tenants = signal<Tenant[]>([]);
  isLoading = signal(true);
  showCreateDialog = signal(false);

  isSuperAdmin = this.adminAuthService.isSuperAdmin;

  // Form data
  newTenant: TenantCreate = { name: '', slug: '' };
  isCreating = signal(false);

  ngOnInit(): void {
    this.loadTenants();
  }

  loadTenants(): void {
    this.isLoading.set(true);
    this.adminApiService.getTenants().subscribe({
      next: (tenants) => {
        this.tenants.set(tenants);
        this.isLoading.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load tenants' });
        this.isLoading.set(false);
      }
    });
  }

  openCreateDialog(): void {
    this.newTenant = { name: '', slug: '' };
    this.showCreateDialog.set(true);
  }

  createTenant(): void {
    if (!this.newTenant.name || !this.newTenant.slug) {
      this.messageService.add({ severity: 'warning', summary: 'Validation', detail: 'Please fill all fields' });
      return;
    }

    this.isCreating.set(true);
    this.adminApiService.createTenant(this.newTenant).subscribe({
      next: (tenant) => {
        this.tenants.update(list => [tenant, ...list]);
        this.showCreateDialog.set(false);
        this.isCreating.set(false);
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Tenant created successfully' });
      },
      error: (err) => {
        this.isCreating.set(false);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to create tenant' });
      }
    });
  }

  toggleTenantStatus(tenant: Tenant): void {
    const newStatus = !tenant.is_active;
    this.adminApiService.updateTenant(tenant.id, { is_active: newStatus }).subscribe({
      next: (updated) => {
        this.tenants.update(list => list.map(t => t.id === updated.id ? updated : t));
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Tenant ${newStatus ? 'activated' : 'deactivated'}`
        });
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to update tenant' });
      }
    });
  }

  confirmDelete(tenant: Tenant): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete "${tenant.name}"? This will also delete all users and data for this tenant.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.deleteTenant(tenant);
      }
    });
  }

  private deleteTenant(tenant: Tenant): void {
    this.adminApiService.deleteTenant(tenant.id).subscribe({
      next: () => {
        this.tenants.update(list => list.filter(t => t.id !== tenant.id));
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Tenant deleted successfully' });
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete tenant' });
      }
    });
  }

  generateSlug(): void {
    if (this.newTenant.name && !this.newTenant.slug) {
      this.newTenant.slug = this.newTenant.name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
    }
  }
}
