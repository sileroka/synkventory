import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { TableModule, TableLazyLoadEvent } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { TagModule } from 'primeng/tag';
import { DialogModule } from 'primeng/dialog';
import { PasswordModule } from 'primeng/password';
import { TooltipModule } from 'primeng/tooltip';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { debounceTime, Subject } from 'rxjs';

import { UserService } from '../../services/user.service';
import { AuthService } from '../../core/services/auth.service';
import {
  IUser,
  UserRole,
  getRoleLabel,
  getRoleSeverity
} from '../../models/user.model';

interface SelectOption {
  label: string;
  value: string | boolean;
}

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    TagModule,
    DialogModule,
    PasswordModule,
    TooltipModule,
    ToastModule,
    ConfirmDialogModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './user-list.component.html',
  styleUrl: './user-list.component.scss'
})
export class UserListComponent implements OnInit {
  private readonly userService = inject(UserService);
  private readonly authService = inject(AuthService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly fb = inject(FormBuilder);
  private readonly searchSubject = new Subject<string>();

  // State
  users: IUser[] = [];
  loading = false;
  saving = false;
  totalRecords = 0;
  currentPage = 1;
  pageSize = 25;

  // Filters
  searchQuery = '';
  statusFilter: boolean | null = null;
  roleFilter: string | null = null;

  // Current user
  currentUserId: string | null = null;
  currentUserRole: UserRole | null = null;

  // Dialogs
  showUserDialog = false;
  showPasswordDialog = false;
  editingUser: IUser | null = null;
  resetPasswordUser: IUser | null = null;

  // Forms
  userForm = this.fb.group({
    name: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(255)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8), Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/)]],
    role: [UserRole.USER, Validators.required]
  });

  passwordForm = this.fb.group({
    newPassword: ['', [Validators.required, Validators.minLength(8), Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/)]]
  });

  // Dropdown options
  statusOptions: SelectOption[] = [
    { label: 'Active', value: true },
    { label: 'Inactive', value: false }
  ];

  roleOptions: SelectOption[] = [
    { label: 'Viewer', value: UserRole.VIEWER },
    { label: 'User', value: UserRole.USER },
    { label: 'Manager', value: UserRole.MANAGER },
    { label: 'Admin', value: UserRole.ADMIN }
  ];

  // Role options for create/edit (filtered based on current user's role)
  createRoleOptions: SelectOption[] = [];

  // Expose helper functions to template
  getRoleLabel = getRoleLabel;
  getRoleSeverity = getRoleSeverity;

  ngOnInit(): void {
    this.setupCurrentUser();
    this.setupSearchDebounce();
    this.loadUsers();
  }

  private setupCurrentUser(): void {
    const currentUser = this.authService.currentUser();
    if (currentUser) {
      this.currentUserId = currentUser.id;
      this.currentUserRole = currentUser.role as UserRole;

      // Set role options based on current user's role
      if (this.currentUserRole === UserRole.ADMIN) {
        this.createRoleOptions = [...this.roleOptions];
      } else if (this.currentUserRole === UserRole.MANAGER) {
        // Managers can't create admins
        this.createRoleOptions = this.roleOptions.filter(r => r.value !== UserRole.ADMIN);
      }
    }
  }

  private setupSearchDebounce(): void {
    this.searchSubject.pipe(debounceTime(300)).subscribe(() => {
      this.currentPage = 1;
      this.loadUsers();
    });
  }

  onSearch(): void {
    this.searchSubject.next(this.searchQuery);
  }

  loadUsers(): void {
    this.loading = true;

    this.userService.getUsers({
      page: this.currentPage,
      pageSize: this.pageSize,
      search: this.searchQuery || undefined,
      isActive: this.statusFilter ?? undefined,
      role: (this.roleFilter as UserRole) || undefined
    }).subscribe({
      next: (response) => {
        this.users = response.items;
        this.totalRecords = response.total;
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load users', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load users'
        });
        this.loading = false;
      }
    });
  }

  onPageChange(event: TableLazyLoadEvent): void {
    this.currentPage = Math.floor((event.first ?? 0) / (event.rows ?? this.pageSize)) + 1;
    this.pageSize = event.rows ?? this.pageSize;
    this.loadUsers();
  }

  showCreateDialog(): void {
    this.editingUser = null;
    this.userForm.reset({ role: UserRole.USER });
    this.userForm.get('password')?.setValidators([
      Validators.required,
      Validators.minLength(8),
      Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/)
    ]);
    this.userForm.get('password')?.updateValueAndValidity();
    this.showUserDialog = true;
  }

  showEditDialog(user: IUser): void {
    this.editingUser = user;
    this.userForm.patchValue({
      name: user.name,
      email: user.email,
      role: user.role,
      password: ''
    });
    // Remove password validation for edit
    this.userForm.get('password')?.clearValidators();
    this.userForm.get('password')?.updateValueAndValidity();
    this.showUserDialog = true;
  }

  hideUserDialog(): void {
    this.showUserDialog = false;
    this.editingUser = null;
    this.userForm.reset();
  }

  saveUser(): void {
    if (this.userForm.invalid) return;

    this.saving = true;
    const formValue = this.userForm.value;

    if (this.editingUser) {
      // Update existing user
      this.userService.updateUser(this.editingUser.id, {
        name: formValue.name ?? undefined,
        role: formValue.role ?? undefined
      }).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'User updated successfully'
          });
          this.hideUserDialog();
          this.loadUsers();
          this.saving = false;
        },
        error: (error) => {
          console.error('Failed to update user', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.error?.detail || 'Failed to update user'
          });
          this.saving = false;
        }
      });
    } else {
      // Create new user
      this.userService.createUser({
        name: formValue.name!,
        email: formValue.email!,
        password: formValue.password!,
        role: formValue.role!
      }).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'User created successfully'
          });
          this.hideUserDialog();
          this.loadUsers();
          this.saving = false;
        },
        error: (error) => {
          console.error('Failed to create user', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.error?.detail || 'Failed to create user'
          });
          this.saving = false;
        }
      });
    }
  }

  confirmDeactivate(user: IUser): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to deactivate ${user.name}? They will no longer be able to log in.`,
      header: 'Confirm Deactivation',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => this.deactivateUser(user)
    });
  }

  deactivateUser(user: IUser): void {
    this.userService.deactivateUser(user.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `${user.name} has been deactivated`
        });
        this.loadUsers();
      },
      error: (error) => {
        console.error('Failed to deactivate user', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.error?.detail || 'Failed to deactivate user'
        });
      }
    });
  }

  activateUser(user: IUser): void {
    this.userService.activateUser(user.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `${user.name} has been activated`
        });
        this.loadUsers();
      },
      error: (error) => {
        console.error('Failed to activate user', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.error?.detail || 'Failed to activate user'
        });
      }
    });
  }

  showResetPasswordDialog(user: IUser): void {
    this.resetPasswordUser = user;
    this.passwordForm.reset();
    this.showPasswordDialog = true;
  }

  hidePasswordDialog(): void {
    this.showPasswordDialog = false;
    this.resetPasswordUser = null;
    this.passwordForm.reset();
  }

  resetPassword(): void {
    if (this.passwordForm.invalid || !this.resetPasswordUser) return;

    this.saving = true;
    const newPassword = this.passwordForm.value.newPassword!;

    this.userService.resetUserPassword(this.resetPasswordUser.id, { newPassword }).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Password reset for ${this.resetPasswordUser?.name}`
        });
        this.hidePasswordDialog();
        this.saving = false;
      },
      error: (error) => {
        console.error('Failed to reset password', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.error?.detail || 'Failed to reset password'
        });
        this.saving = false;
      }
    });
  }
}
