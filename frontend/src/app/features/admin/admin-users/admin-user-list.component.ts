import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { CheckboxModule } from 'primeng/checkbox';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { MessageService, ConfirmationService } from 'primeng/api';
import { AdminApiService, AdminUser, AdminUserCreate } from '../../../core/services/admin-api.service';

@Component({
  selector: 'app-admin-user-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    CheckboxModule,
    TagModule,
    TooltipModule,
    ConfirmDialogModule,
    ToastModule,
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast />
    <p-confirmDialog />

    <div class="admin-users-container">
      <div class="page-header">
        <h1>Admin Users</h1>
        <p-button
          label="Add Admin User"
          icon="pi pi-plus"
          (onClick)="showAddDialog()"
        />
      </div>

      <p-table
        [value]="adminUsers()"
        [loading]="loading()"
        styleClass="p-datatable-striped"
        responsiveLayout="scroll"
      >
        <ng-template pTemplate="header">
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Last Login</th>
            <th>Actions</th>
          </tr>
        </ng-template>
        <ng-template pTemplate="body" let-admin>
          <tr>
            <td>{{ admin.name }}</td>
            <td>{{ admin.email }}</td>
            <td>
              <p-tag
                [value]="admin.is_super_admin ? 'Super Admin' : 'Admin'"
                [severity]="admin.is_super_admin ? 'danger' : 'info'"
              />
            </td>
            <td>
              <p-tag
                [value]="admin.is_active ? 'Active' : 'Inactive'"
                [severity]="admin.is_active ? 'success' : 'secondary'"
              />
            </td>
            <td>{{ admin.last_login ? (admin.last_login | date:'short') : 'Never' }}</td>
            <td>
              <p-button
                icon="pi pi-pencil"
                [rounded]="true"
                [text]="true"
                pTooltip="Edit"
                (onClick)="editAdmin(admin)"
              />
              <p-button
                [icon]="admin.is_active ? 'pi pi-ban' : 'pi pi-check'"
                [rounded]="true"
                [text]="true"
                [severity]="admin.is_active ? 'warning' : 'success'"
                [pTooltip]="admin.is_active ? 'Deactivate' : 'Activate'"
                (onClick)="toggleStatus(admin)"
              />
            </td>
          </tr>
        </ng-template>
        <ng-template pTemplate="emptymessage">
          <tr>
            <td colspan="6" class="text-center">No admin users found.</td>
          </tr>
        </ng-template>
      </p-table>
    </div>

    <!-- Add/Edit Dialog -->
    <p-dialog
      [(visible)]="displayDialog"
      [header]="isEditing ? 'Edit Admin User' : 'Add Admin User'"
      [modal]="true"
      [style]="{ width: '450px' }"
    >
      <div class="dialog-content">
        <div class="field">
          <label for="name">Name</label>
          <input pInputText id="name" [(ngModel)]="formData.name" class="w-full" />
        </div>
        <div class="field">
          <label for="email">Email</label>
          <input pInputText id="email" [(ngModel)]="formData.email" class="w-full" [disabled]="isEditing" />
        </div>
        @if (!isEditing) {
          <div class="field">
            <label for="password">Password</label>
            <input pInputText id="password" type="password" [(ngModel)]="formData.password" class="w-full" />
          </div>
        }
        <div class="field-checkbox">
          <p-checkbox [(ngModel)]="formData.is_super_admin" [binary]="true" inputId="superAdmin" />
          <label for="superAdmin" class="ml-2">Super Admin</label>
        </div>
      </div>
      <ng-template pTemplate="footer">
        <p-button label="Cancel" icon="pi pi-times" [text]="true" (onClick)="displayDialog = false" />
        <p-button label="Save" icon="pi pi-check" (onClick)="saveAdmin()" [loading]="saving()" />
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .admin-users-container {
      padding: 1.5rem;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;

      h1 {
        margin: 0;
        font-size: 1.5rem;
        color: var(--text-color);
      }
    }

    .dialog-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;

      label {
        font-weight: 500;
      }
    }

    .field-checkbox {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .text-center {
      text-align: center;
      padding: 2rem;
      color: var(--text-color-secondary);
    }
  `]
})
export class AdminUserListComponent implements OnInit {
  private adminApiService = inject(AdminApiService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  adminUsers = signal<AdminUser[]>([]);
  loading = signal(true);
  saving = signal(false);
  displayDialog = false;
  isEditing = false;
  editingId: string | null = null;

  formData = {
    name: '',
    email: '',
    password: '',
    is_super_admin: false,
  };

  ngOnInit(): void {
    this.loadAdminUsers();
  }

  loadAdminUsers(): void {
    this.loading.set(true);
    this.adminApiService.getAdminUsers().subscribe({
      next: (users) => {
        this.adminUsers.set(users);
        this.loading.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load admin users' });
        this.loading.set(false);
      }
    });
  }

  showAddDialog(): void {
    this.isEditing = false;
    this.editingId = null;
    this.formData = { name: '', email: '', password: '', is_super_admin: false };
    this.displayDialog = true;
  }

  editAdmin(admin: AdminUser): void {
    this.isEditing = true;
    this.editingId = admin.id;
    this.formData = {
      name: admin.name,
      email: admin.email,
      password: '',
      is_super_admin: admin.is_super_admin,
    };
    this.displayDialog = true;
  }

  saveAdmin(): void {
    if (!this.formData.name || !this.formData.email) {
      this.messageService.add({ severity: 'warn', summary: 'Validation', detail: 'Name and email are required' });
      return;
    }

    if (!this.isEditing && !this.formData.password) {
      this.messageService.add({ severity: 'warn', summary: 'Validation', detail: 'Password is required' });
      return;
    }

    this.saving.set(true);

    if (this.isEditing && this.editingId) {
      this.adminApiService.updateAdminUser(this.editingId, {
        name: this.formData.name,
        is_super_admin: this.formData.is_super_admin,
      }).subscribe({
        next: (updated) => {
          this.adminUsers.update(list => list.map(u => u.id === updated.id ? updated : u));
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Admin user updated' });
          this.displayDialog = false;
          this.saving.set(false);
        },
        error: () => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to update admin user' });
          this.saving.set(false);
        }
      });
    } else {
      const data: AdminUserCreate = {
        name: this.formData.name,
        email: this.formData.email,
        password: this.formData.password,
        is_super_admin: this.formData.is_super_admin,
      };

      this.adminApiService.createAdminUser(data).subscribe({
        next: (user) => {
          this.adminUsers.update(list => [user, ...list]);
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Admin user created' });
          this.displayDialog = false;
          this.saving.set(false);
        },
        error: () => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to create admin user' });
          this.saving.set(false);
        }
      });
    }
  }

  toggleStatus(admin: AdminUser): void {
    const newStatus = !admin.is_active;
    const action = newStatus ? 'activate' : 'deactivate';

    this.confirmationService.confirm({
      message: `Are you sure you want to ${action} "${admin.name}"?`,
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.adminApiService.updateAdminUser(admin.id, { is_active: newStatus }).subscribe({
          next: (updated) => {
            this.adminUsers.update(list => list.map(u => u.id === updated.id ? updated : u));
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: `Admin user ${newStatus ? 'activated' : 'deactivated'}`
            });
          },
          error: () => {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to update status' });
          }
        });
      }
    });
  }
}
