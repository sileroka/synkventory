import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

// PrimeNG Modules
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { CardModule } from 'primeng/card';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { CalendarModule } from 'primeng/calendar';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { AutoCompleteModule, AutoCompleteCompleteEvent } from 'primeng/autocomplete';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';

import { WorkOrderService, IWorkOrderFilters } from '../../services/work-order.service';
import { InventoryService } from '../../services/inventory.service';
import { LocationService } from '../locations/services/location.service';
import { UserService } from '../../services/user.service';
import { BomService } from '../../services/bom.service';
import {
  IWorkOrderListItem,
  IWorkOrderCreate,
  IWorkOrderStats,
  WorkOrderStatus,
  WorkOrderPriority,
  WorkOrderHelpers,
} from '../../models/work-order.model';
import { IInventoryItem } from '../../models/inventory-item.model';
import { ILocation } from '../locations/models/location.model';
import { IUser } from '../../models/user.model';

interface IAssemblyItem extends IInventoryItem {
  hasBom?: boolean;
}

@Component({
  selector: 'app-work-order-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    TooltipModule,
    TagModule,
    CardModule,
    ProgressSpinnerModule,
    ProgressBarModule,
    ToastModule,
    DialogModule,
    InputNumberModule,
    CalendarModule,
    InputTextareaModule,
    AutoCompleteModule,
    ConfirmDialogModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './work-order-list.component.html',
  styleUrls: ['./work-order-list.component.scss'],
})
export class WorkOrderListComponent implements OnInit {
  // State
  workOrders = signal<IWorkOrderListItem[]>([]);
  stats = signal<IWorkOrderStats | null>(null);
  isLoading = signal(true);
  
  // Pagination
  page = 1;
  pageSize = 25;
  totalRecords = 0;
  
  // Filters
  statusFilter: WorkOrderStatus | null = null;
  priorityFilter: WorkOrderPriority | null = null;
  includeCompleted = false;
  
  statusOptions = [
    { label: 'All Active', value: null },
    { label: 'Draft', value: WorkOrderStatus.DRAFT },
    { label: 'Pending', value: WorkOrderStatus.PENDING },
    { label: 'In Progress', value: WorkOrderStatus.IN_PROGRESS },
    { label: 'On Hold', value: WorkOrderStatus.ON_HOLD },
    { label: 'Completed', value: WorkOrderStatus.COMPLETED },
    { label: 'Cancelled', value: WorkOrderStatus.CANCELLED },
  ];
  
  priorityOptions = [
    { label: 'All Priorities', value: null },
    { label: 'Low', value: WorkOrderPriority.LOW },
    { label: 'Normal', value: WorkOrderPriority.NORMAL },
    { label: 'High', value: WorkOrderPriority.HIGH },
    { label: 'Urgent', value: WorkOrderPriority.URGENT },
  ];
  
  // Create dialog
  showCreateDialog = signal(false);
  assemblySuggestions = signal<IAssemblyItem[]>([]);
  selectedAssembly = signal<IAssemblyItem | null>(null);
  locations = signal<ILocation[]>([]);
  users = signal<IUser[]>([]);
  
  newWorkOrder: IWorkOrderCreate = {
    itemId: '',
    quantityOrdered: 1,
    priority: WorkOrderPriority.NORMAL,
  };
  
  // Helpers
  helpers = WorkOrderHelpers;

  constructor(
    private workOrderService: WorkOrderService,
    private inventoryService: InventoryService,
    private locationService: LocationService,
    private userService: UserService,
    private bomService: BomService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadWorkOrders();
    this.loadStats();
  }

  async loadWorkOrders(): Promise<void> {
    this.isLoading.set(true);
    try {
      const filters: IWorkOrderFilters = {};
      if (this.statusFilter) filters.status = this.statusFilter;
      if (this.priorityFilter) filters.priority = this.priorityFilter;
      if (this.includeCompleted) filters.includeCompleted = true;
      
      const result = await this.workOrderService.getWorkOrders(
        this.page,
        this.pageSize,
        filters
      ).toPromise();
      
      this.workOrders.set(result?.items ?? []);
      this.totalRecords = result?.pagination.totalItems ?? 0;
    } catch (error) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load work orders',
      });
    } finally {
      this.isLoading.set(false);
    }
  }

  async loadStats(): Promise<void> {
    try {
      const stats = await this.workOrderService.getStats().toPromise();
      this.stats.set(stats ?? null);
    } catch {
      // Stats are optional, don't show error
    }
  }

  onPageChange(event: any): void {
    this.page = Math.floor(event.first / event.rows) + 1;
    this.pageSize = event.rows;
    this.loadWorkOrders();
  }

  onFilterChange(): void {
    this.page = 1;
    this.loadWorkOrders();
  }

  // Create dialog methods
  openCreateDialog(): void {
    this.newWorkOrder = {
      itemId: '',
      quantityOrdered: 1,
      priority: WorkOrderPriority.NORMAL,
    };
    this.selectedAssembly.set(null);
    this.loadLocations();
    this.loadUsers();
    this.showCreateDialog.set(true);
  }

  async loadLocations(): Promise<void> {
    try {
      const result = await this.locationService.getLocations().toPromise();
      this.locations.set(result?.items ?? []);
    } catch {
      // Ignore
    }
  }

  async loadUsers(): Promise<void> {
    try {
      const result = await this.userService.getUsers().toPromise();
      this.users.set(result?.items ?? []);
    } catch {
      // Ignore
    }
  }

  async searchAssemblies(event: AutoCompleteCompleteEvent): Promise<void> {
    const query = event.query.toLowerCase();
    try {
      // Get items matching query
      const result = await this.inventoryService.getItems(1, 50, { search: query }).toPromise();
      const items = result?.items ?? [];
      
      // Filter to only items that have BOMs
      const assemblies: IAssemblyItem[] = [];
      for (const item of items) {
        if (!item.id) continue;
        try {
          const bom = await this.bomService.getItemBom(item.id).toPromise();
          if (bom && bom.length > 0) {
            assemblies.push({ ...item, hasBom: true });
          }
        } catch {
          // No BOM
        }
      }
      
      this.assemblySuggestions.set(assemblies);
    } catch {
      this.assemblySuggestions.set([]);
    }
  }

  onAssemblySelect(event: any): void {
    const item = event.value || event;
    this.selectedAssembly.set(item);
    if (item?.id) {
      this.newWorkOrder.itemId = item.id;
    }
  }

  async createWorkOrder(): Promise<void> {
    if (!this.newWorkOrder.itemId) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Please select an assembly item',
      });
      return;
    }

    try {
      await this.workOrderService.createWorkOrder(this.newWorkOrder).toPromise();
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Work order created successfully',
      });
      this.showCreateDialog.set(false);
      this.loadWorkOrders();
      this.loadStats();
    } catch (error: any) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: error.error?.detail || 'Failed to create work order',
      });
    }
  }

  viewWorkOrder(wo: IWorkOrderListItem): void {
    this.router.navigate(['/work-orders', wo.id]);
  }

  confirmDelete(wo: IWorkOrderListItem): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete work order ${wo.workOrderNumber}?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      accept: async () => {
        try {
          await this.workOrderService.deleteWorkOrder(wo.id).toPromise();
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Work order deleted',
          });
          this.loadWorkOrders();
          this.loadStats();
        } catch (error: any) {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.error?.detail || 'Failed to delete work order',
          });
        }
      },
    });
  }

  canDelete(wo: IWorkOrderListItem): boolean {
    return wo.status === WorkOrderStatus.DRAFT || wo.status === WorkOrderStatus.CANCELLED;
  }

  getProgressColor(wo: IWorkOrderListItem): string {
    if (wo.completionPercentage >= 100) return '#10B981';
    if (wo.isOverdue) return '#EF4444';
    if (wo.completionPercentage > 50) return '#0D9488';
    return '#F59E0B';
  }
}
