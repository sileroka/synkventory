import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { DropdownModule } from 'primeng/dropdown';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { AdminApiService, Tenant, TenantUser, TenantUserCreate } from '../../../core/services/admin-api.service';

@Component({
  selector: 'app-tenant-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    PasswordModule,
    DropdownModule,
    TagModule,
    ToastModule,
    TooltipModule,
    ConfirmDialogModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './tenant-detail.component.html',
  styleUrl: './tenant-detail.component.scss'
})
export class TenantDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private adminApiService = inject(AdminApiService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  tenantId = '';
  tenant = signal<Tenant | null>(null);
  users = signal<TenantUser[]>([]);
  isLoading = signal(true);

  showCreateDialog = signal(false);
  isCreating = signal(false);

  newUser: TenantUserCreate = { email: '', name: '', password: '', role: 'user' };

  roleOptions = [
    { label: 'Viewer', value: 'viewer' },
    { label: 'User', value: 'user' },
    { label: 'Manager', value: 'manager' },
    { label: 'Admin', value: 'admin' },
  ];

  ngOnInit(): void {
    this.tenantId = this.route.snapshot.paramMap.get('id') || '';
    this.loadTenant();
    this.loadUsers();
  }

  loadTenant(): void {
    this.adminApiService.getTenant(this.tenantId).subscribe({
      next: (tenant) => this.tenant.set(tenant),
      error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load tenant' })
    });
  }

  loadUsers(): void {
    this.isLoading.set(true);
    this.adminApiService.getTenantUsers(this.tenantId).subscribe({
      next: (users) => {
        this.users.set(users);
        this.isLoading.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load users' });
        this.isLoading.set(false);
      }
    });
  }

  openCreateDialog(): void {
    this.newUser = { email: '', name: '', password: '', role: 'user' };
    this.showCreateDialog.set(true);
  }

  createUser(): void {
    if (!this.newUser.email || !this.newUser.name || !this.newUser.password) {
      this.messageService.add({ severity: 'warning', summary: 'Validation', detail: 'Please fill all required fields' });
      return;
    }

    this.isCreating.set(true);
    this.adminApiService.createTenantUser(this.tenantId, this.newUser).subscribe({
      next: (user) => {
        this.users.update(list => [user, ...list]);
        this.showCreateDialog.set(false);
        this.isCreating.set(false);
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'User created successfully' });
      },
      error: (err) => {
        this.isCreating.set(false);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to create user' });
      }
    });
  }

  toggleUserStatus(user: TenantUser): void {
    const newStatus = !user.is_active;
    this.adminApiService.updateTenantUser(this.tenantId, user.id, { is_active: newStatus }).subscribe({
      next: (updated) => {
        this.users.update(list => list.map(u => u.id === updated.id ? updated : u));
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `User ${newStatus ? 'activated' : 'deactivated'}`
        });
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to update user' });
      }
    });
  }

  updateUserRole(user: TenantUser, newRole: string): void {
    this.adminApiService.updateTenantUser(this.tenantId, user.id, { role: newRole }).subscribe({
      next: (updated) => {
        this.users.update(list => list.map(u => u.id === updated.id ? updated : u));
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Role updated' });
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to update role' });
      }
    });
  }

  confirmDelete(user: TenantUser): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete user "${user.name}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => this.deleteUser(user)
    });
  }

  private deleteUser(user: TenantUser): void {
    this.adminApiService.deleteTenantUser(this.tenantId, user.id).subscribe({
      next: () => {
        this.users.update(list => list.filter(u => u.id !== user.id));
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'User deleted' });
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete user' });
      }
    });
  }

  getRoleSeverity(role: string): 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast' | undefined {
    switch (role) {
      case 'admin': return 'danger';
      case 'manager': return 'warning';
      case 'user': return 'info';
      default: return 'secondary';
    }
  }
}
