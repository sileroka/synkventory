/**
 * Work Order TypeScript models.
 */

/**
 * Work order status values.
 */
export enum WorkOrderStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  ON_HOLD = 'on_hold',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

/**
 * Work order priority levels.
 */
export enum WorkOrderPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent',
}

/**
 * Summary of the item being built.
 */
export interface IWorkOrderItemSummary {
  id: string;
  sku: string;
  name: string;
  totalQuantity?: number;
}

/**
 * Summary of a location.
 */
export interface IWorkOrderLocationSummary {
  id: string;
  name: string;
  code?: string;
}

/**
 * Summary of a user.
 */
export interface IWorkOrderUserSummary {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
}

/**
 * Full work order interface.
 */
export interface IWorkOrder {
  id: string;
  workOrderNumber: string;
  
  // Item info
  itemId: string;
  item?: IWorkOrderItemSummary;
  
  // Quantities
  quantityOrdered: number;
  quantityCompleted: number;
  quantityScrapped: number;
  quantityRemaining?: number;
  completionPercentage?: number;
  
  // Status and priority
  status: WorkOrderStatus;
  priority: WorkOrderPriority;
  
  // Dates
  dueDate?: string;
  startDate?: string;
  completedDate?: string;
  isOverdue?: boolean;
  
  // Location and assignment
  outputLocationId?: string;
  outputLocation?: IWorkOrderLocationSummary;
  assignedToId?: string;
  assignedTo?: IWorkOrderUserSummary;
  
  // Notes
  description?: string;
  notes?: string;
  
  // Cost
  estimatedCost?: number;
  actualCost?: number;
  
  // Audit
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

/**
 * Work order list item (summary).
 */
export interface IWorkOrderListItem {
  id: string;
  workOrderNumber: string;
  itemId: string;
  itemSku?: string;
  itemName?: string;
  quantityOrdered: number;
  quantityCompleted: number;
  quantityRemaining: number;
  completionPercentage: number;
  status: WorkOrderStatus;
  priority: WorkOrderPriority;
  dueDate?: string;
  isOverdue: boolean;
  assignedToName?: string;
  createdAt: string;
}

/**
 * Request to create a work order.
 */
export interface IWorkOrderCreate {
  itemId: string;
  quantityOrdered: number;
  priority?: WorkOrderPriority;
  dueDate?: string;
  outputLocationId?: string;
  assignedToId?: string;
  description?: string;
  notes?: string;
}

/**
 * Request to update a work order.
 */
export interface IWorkOrderUpdate {
  quantityOrdered?: number;
  priority?: WorkOrderPriority;
  dueDate?: string;
  outputLocationId?: string;
  assignedToId?: string;
  description?: string;
  notes?: string;
}

/**
 * Request to update work order status.
 */
export interface IWorkOrderStatusUpdate {
  status: WorkOrderStatus;
  notes?: string;
}

/**
 * Request to record production progress.
 */
export interface IWorkOrderProgressUpdate {
  quantityCompleted: number;
  quantityScrapped?: number;
  notes?: string;
}

/**
 * Request to build items for a work order.
 */
export interface IWorkOrderBuildRequest {
  quantity: number;
  notes?: string;
}

/**
 * Work order statistics.
 */
export interface IWorkOrderStats {
  total: number;
  draft: number;
  pending: number;
  inProgress: number;
  onHold: number;
  completed: number;
  cancelled: number;
  overdue: number;
}

/**
 * Helper functions for work orders.
 */
export const WorkOrderHelpers = {
  /**
   * Get status label for display.
   */
  getStatusLabel(status: WorkOrderStatus): string {
    const labels: Record<WorkOrderStatus, string> = {
      [WorkOrderStatus.DRAFT]: 'Draft',
      [WorkOrderStatus.PENDING]: 'Pending',
      [WorkOrderStatus.IN_PROGRESS]: 'In Progress',
      [WorkOrderStatus.ON_HOLD]: 'On Hold',
      [WorkOrderStatus.COMPLETED]: 'Completed',
      [WorkOrderStatus.CANCELLED]: 'Cancelled',
    };
    return labels[status] || status;
  },

  /**
   * Get status severity for PrimeNG tag.
   */
  getStatusSeverity(status: WorkOrderStatus): 'success' | 'info' | 'warning' | 'danger' | 'secondary' {
    const severities: Record<WorkOrderStatus, 'success' | 'info' | 'warning' | 'danger' | 'secondary'> = {
      [WorkOrderStatus.DRAFT]: 'secondary',
      [WorkOrderStatus.PENDING]: 'info',
      [WorkOrderStatus.IN_PROGRESS]: 'warning',
      [WorkOrderStatus.ON_HOLD]: 'warning',
      [WorkOrderStatus.COMPLETED]: 'success',
      [WorkOrderStatus.CANCELLED]: 'danger',
    };
    return severities[status] || 'secondary';
  },

  /**
   * Get priority label for display.
   */
  getPriorityLabel(priority: WorkOrderPriority): string {
    const labels: Record<WorkOrderPriority, string> = {
      [WorkOrderPriority.LOW]: 'Low',
      [WorkOrderPriority.NORMAL]: 'Normal',
      [WorkOrderPriority.HIGH]: 'High',
      [WorkOrderPriority.URGENT]: 'Urgent',
    };
    return labels[priority] || priority;
  },

  /**
   * Get priority severity for PrimeNG tag.
   */
  getPrioritySeverity(priority: WorkOrderPriority): 'success' | 'info' | 'warning' | 'danger' | 'secondary' {
    const severities: Record<WorkOrderPriority, 'success' | 'info' | 'warning' | 'danger' | 'secondary'> = {
      [WorkOrderPriority.LOW]: 'secondary',
      [WorkOrderPriority.NORMAL]: 'info',
      [WorkOrderPriority.HIGH]: 'warning',
      [WorkOrderPriority.URGENT]: 'danger',
    };
    return severities[priority] || 'secondary';
  },

  /**
   * Check if a status transition is valid.
   */
  canTransitionTo(currentStatus: WorkOrderStatus, newStatus: WorkOrderStatus): boolean {
    const validTransitions: Record<WorkOrderStatus, WorkOrderStatus[]> = {
      [WorkOrderStatus.DRAFT]: [WorkOrderStatus.PENDING, WorkOrderStatus.CANCELLED],
      [WorkOrderStatus.PENDING]: [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.ON_HOLD, WorkOrderStatus.CANCELLED],
      [WorkOrderStatus.IN_PROGRESS]: [WorkOrderStatus.ON_HOLD, WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED],
      [WorkOrderStatus.ON_HOLD]: [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED],
      [WorkOrderStatus.COMPLETED]: [],
      [WorkOrderStatus.CANCELLED]: [],
    };
    return validTransitions[currentStatus]?.includes(newStatus) ?? false;
  },
};
