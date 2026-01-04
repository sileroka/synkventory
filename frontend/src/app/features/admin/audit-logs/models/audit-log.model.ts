/**
 * Audit log models for admin portal.
 */

export interface IAuditLog {
  id: string;
  tenantId: string;
  tenantName?: string;
  userId?: string;
  userEmail?: string;
  action: string;
  entityType: string;
  entityId?: string;
  entityName?: string;
  extraData?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  createdAt: string;
}

export interface IAuditLogListResponse {
  data: IAuditLog[];
  meta: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

export interface IAuditLogFilters {
  tenantId?: string;
  userId?: string;
  action?: string;
  entityType?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
}

export enum AuditAction {
  // Authentication
  LOGIN = 'LOGIN',
  LOGOUT = 'LOGOUT',
  LOGIN_FAILED = 'LOGIN_FAILED',
  PASSWORD_CHANGE = 'PASSWORD_CHANGE',
  PASSWORD_RESET = 'PASSWORD_RESET',
  
  // CRUD
  CREATE = 'CREATE',
  READ = 'READ',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
  
  // Stock operations
  STOCK_RECEIVE = 'STOCK_RECEIVE',
  STOCK_SHIP = 'STOCK_SHIP',
  STOCK_TRANSFER = 'STOCK_TRANSFER',
  STOCK_ADJUST = 'STOCK_ADJUST',
  STOCK_COUNT = 'STOCK_COUNT',
  
  // Bulk operations
  BULK_DELETE = 'BULK_DELETE',
  BULK_UPDATE = 'BULK_UPDATE',
  BULK_IMPORT = 'BULK_IMPORT',
  BULK_EXPORT = 'BULK_EXPORT',
  
  // User management
  USER_ACTIVATE = 'USER_ACTIVATE',
  USER_DEACTIVATE = 'USER_DEACTIVATE',
  USER_LOCK = 'USER_LOCK',
  USER_UNLOCK = 'USER_UNLOCK',
  
  // Navigation
  PAGE_VIEW = 'PAGE_VIEW',
}

export enum EntityType {
  USER = 'USER',
  TENANT = 'TENANT',
  INVENTORY_ITEM = 'INVENTORY_ITEM',
  CATEGORY = 'CATEGORY',
  LOCATION = 'LOCATION',
  STOCK_MOVEMENT = 'STOCK_MOVEMENT',
  REPORT = 'REPORT',
  SYSTEM = 'SYSTEM',
}

/**
 * Action display labels for UI.
 */
export const ActionLabels: Record<string, string> = {
  [AuditAction.LOGIN]: 'User Login',
  [AuditAction.LOGOUT]: 'User Logout',
  [AuditAction.LOGIN_FAILED]: 'Failed Login',
  [AuditAction.PASSWORD_CHANGE]: 'Password Changed',
  [AuditAction.PASSWORD_RESET]: 'Password Reset',
  [AuditAction.CREATE]: 'Created',
  [AuditAction.READ]: 'Viewed',
  [AuditAction.UPDATE]: 'Updated',
  [AuditAction.DELETE]: 'Deleted',
  [AuditAction.STOCK_RECEIVE]: 'Stock Received',
  [AuditAction.STOCK_SHIP]: 'Stock Shipped',
  [AuditAction.STOCK_TRANSFER]: 'Stock Transferred',
  [AuditAction.STOCK_ADJUST]: 'Stock Adjusted',
  [AuditAction.STOCK_COUNT]: 'Stock Count',
  [AuditAction.BULK_DELETE]: 'Bulk Delete',
  [AuditAction.BULK_UPDATE]: 'Bulk Update',
  [AuditAction.BULK_IMPORT]: 'Bulk Import',
  [AuditAction.BULK_EXPORT]: 'Bulk Export',
  [AuditAction.USER_ACTIVATE]: 'User Activated',
  [AuditAction.USER_DEACTIVATE]: 'User Deactivated',
  [AuditAction.USER_LOCK]: 'User Locked',
  [AuditAction.USER_UNLOCK]: 'User Unlocked',
  [AuditAction.PAGE_VIEW]: 'Page Viewed',
};
