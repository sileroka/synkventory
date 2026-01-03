/**
 * User model and related interfaces.
 */

export enum UserRole {
  VIEWER = 'viewer',
  USER = 'user',
  MANAGER = 'manager',
  ADMIN = 'admin'
}

export interface IUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  isActive: boolean;
  isLocked: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface IUserCreate {
  email: string;
  name: string;
  password: string;
  role: UserRole;
}

export interface IUserUpdate {
  name?: string;
  role?: UserRole;
  isActive?: boolean;
}

export interface IUserListResponse {
  items: IUser[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface IPasswordChange {
  currentPassword: string;
  newPassword: string;
}

export interface IPasswordReset {
  newPassword: string;
}

export interface IUserFilters {
  search?: string;
  isActive?: boolean;
  role?: UserRole;
  page?: number;
  pageSize?: number;
}

/**
 * Helper function to get display label for a role.
 */
export function getRoleLabel(role: UserRole): string {
  switch (role) {
    case UserRole.VIEWER:
      return 'Viewer';
    case UserRole.USER:
      return 'User';
    case UserRole.MANAGER:
      return 'Manager';
    case UserRole.ADMIN:
      return 'Admin';
    default:
      return role;
  }
}

/**
 * Helper function to get severity for role badge.
 */
export function getRoleSeverity(role: UserRole): 'success' | 'info' | 'warning' | 'danger' | 'secondary' {
  switch (role) {
    case UserRole.ADMIN:
      return 'danger';
    case UserRole.MANAGER:
      return 'warning';
    case UserRole.USER:
      return 'info';
    case UserRole.VIEWER:
      return 'secondary';
    default:
      return 'secondary';
  }
}
