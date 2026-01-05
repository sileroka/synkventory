import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

// PrimeNG Modules
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressBarModule } from 'primeng/progressbar';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DividerModule } from 'primeng/divider';
import { TimelineModule } from 'primeng/timeline';
import { TableModule } from 'primeng/table';
import { MessageService, ConfirmationService } from 'primeng/api';

import { WorkOrderService } from '../../services/work-order.service';
import { BomService } from '../../services/bom.service';
import { LocationService } from '../locations/services/location.service';
import { UserService } from '../../services/user.service';
import {
  IWorkOrder,
  IWorkOrderUpdate,
  WorkOrderStatus,
  WorkOrderPriority,
  WorkOrderHelpers,
} from '../../models/work-order.model';
import { IBillOfMaterial, IBOMAvailability } from '../../models/bill-of-material.model';
import { ILocation } from '../locations/models/location.model';
import { IUser } from '../../models/user.model';

@Component({
  selector: 'app-work-order-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    ButtonModule,
    CardModule,
    TagModule,
    TooltipModule,
    ProgressBarModule,
    ProgressSpinnerModule,
    DialogModule,
    InputNumberModule,
    InputTextareaModule,
    DropdownModule,
    CalendarModule,
    ToastModule,
    ConfirmDialogModule,
    DividerModule,
    TimelineModule,
    TableModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './work-order-detail.component.html',
  styleUrls: ['./work-order-detail.component.scss'],
})
export class WorkOrderDetailComponent implements OnInit {
  // State
  workOrder = signal<IWorkOrder | null>(null);
  bomComponents = signal<IBillOfMaterial[]>([]);
  availability = signal<IBOMAvailability | null>(null);
  isLoading = signal(true);
  
  // Reference data
  locations = signal<ILocation[]>([]);
  users = signal<IUser[]>([]);
  
  // Dialogs
  showEditDialog = signal(false);
  showProgressDialog = signal(false);
  showBuildDialog = signal(false);
  showStatusDialog = signal(false);
  
  // Edit form
  editForm: IWorkOrderUpdate = {};
  
  // Progress form
  progressQuantityCompleted = 0;
  progressQuantityScrapped = 0;
  progressNotes = '';
  
  // Build form
  buildQuantity = 1;
  buildNotes = '';
  
  // Status form
  newStatus: WorkOrderStatus | null = null;
  statusNotes = '';
  
  // Helpers
  helpers = WorkOrderHelpers;
  
  // Computed
  canEdit = computed(() => {
    const wo = this.workOrder();
    return wo && ![WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED].includes(wo.status);
  });
  
  canBuild = computed(() => {
    const wo = this.workOrder();
    const avail = this.availability();
    return wo && 
      [WorkOrderStatus.PENDING, WorkOrderStatus.IN_PROGRESS].includes(wo.status) &&
      avail && avail.maxBuildable > 0 &&
      (wo.quantityRemaining ?? 0) > 0;
  });
  
  maxBuildQuantity = computed(() => {
    const wo = this.workOrder();
    const avail = this.availability();
    if (!wo || !avail) return 0;
    return Math.min(avail.maxBuildable, wo.quantityRemaining ?? 0);
  });
  
  statusOptions = computed(() => {
    const wo = this.workOrder();
    if (!wo) return [];
    
    const options: { label: string; value: WorkOrderStatus }[] = [];
    const allStatuses = [
      WorkOrderStatus.PENDING,
      WorkOrderStatus.IN_PROGRESS,
      WorkOrderStatus.ON_HOLD,
      WorkOrderStatus.COMPLETED,
      WorkOrderStatus.CANCELLED,
    ];
    
    for (const status of allStatuses) {
      if (this.helpers.canTransitionTo(wo.status, status)) {
        options.push({
          label: this.helpers.getStatusLabel(status),
          value: status,
        });
      }
    }
    
    return options;
  });

  constructor(
    private route: ActivatedRoute,
    public router: Router,
    private workOrderService: WorkOrderService,
    private bomService: BomService,
    private locationService: LocationService,
    private userService: UserService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadWorkOrder(id);
      this.loadReferenceData();
    }
  }

  async loadWorkOrder(id: string): Promise<void> {
    this.isLoading.set(true);
    try {
      const wo = await this.workOrderService.getWorkOrder(id).toPromise();
      this.workOrder.set(wo ?? null);
      
      if (wo?.itemId) {
        this.loadBomData(wo.itemId);
      }
    } catch (error) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load work order',
      });
      this.router.navigate(['/work-orders']);
    } finally {
      this.isLoading.set(false);
    }
  }

  async loadBomData(itemId: string): Promise<void> {
    try {
      const [components, availability] = await Promise.all([
        this.bomService.getItemBom(itemId).toPromise(),
        this.bomService.getBuildAvailability(itemId).toPromise(),
      ]);
      this.bomComponents.set(components ?? []);
      this.availability.set(availability ?? null);
    } catch {
      // BOM data is optional
    }
  }

  async loadReferenceData(): Promise<void> {
    try {
      const [locationsResult, usersResult] = await Promise.all([
        this.locationService.getLocations().toPromise(),
        this.userService.getUsers().toPromise(),
      ]);
      this.locations.set(locationsResult?.items ?? []);
      this.users.set(usersResult?.items ?? []);
    } catch {
      // Reference data is optional
    }
  }

  // Edit dialog
  openEditDialog(): void {
    const wo = this.workOrder();
    if (!wo) return;
    
    this.editForm = {
      quantityOrdered: wo.quantityOrdered,
      priority: wo.priority,
      dueDate: wo.dueDate,
      outputLocationId: wo.outputLocationId,
      assignedToId: wo.assignedToId,
      description: wo.description,
      notes: wo.notes,
    };
    this.showEditDialog.set(true);
  }

  async saveEdit(): Promise<void> {
    const wo = this.workOrder();
    if (!wo) return;
    
    try {
      const updated = await this.workOrderService.updateWorkOrder(wo.id, this.editForm).toPromise();
      this.workOrder.set(updated ?? null);
      this.showEditDialog.set(false);
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Work order updated',
      });
    } catch (error: any) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: error.error?.detail || 'Failed to update work order',
      });
    }
  }

  // Status dialog
  openStatusDialog(): void {
    this.newStatus = null;
    this.statusNotes = '';
    this.showStatusDialog.set(true);
  }

  async updateStatus(): Promise<void> {
    const wo = this.workOrder();
    if (!wo || !this.newStatus) return;
    
    try {
      const updated = await this.workOrderService.updateStatus(wo.id, {
        status: this.newStatus,
        notes: this.statusNotes,
      }).toPromise();
      this.workOrder.set(updated ?? null);
      this.showStatusDialog.set(false);
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: `Status updated to ${this.helpers.getStatusLabel(this.newStatus)}`,
      });
    } catch (error: any) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: error.error?.detail || 'Failed to update status',
      });
    }
  }

  // Progress dialog
  openProgressDialog(): void {
    const wo = this.workOrder();
    if (!wo) return;
    
    this.progressQuantityCompleted = wo.quantityCompleted;
    this.progressQuantityScrapped = wo.quantityScrapped;
    this.progressNotes = '';
    this.showProgressDialog.set(true);
  }

  async recordProgress(): Promise<void> {
    const wo = this.workOrder();
    if (!wo) return;
    
    try {
      const updated = await this.workOrderService.recordProgress(wo.id, {
        quantityCompleted: this.progressQuantityCompleted,
        quantityScrapped: this.progressQuantityScrapped,
        notes: this.progressNotes,
      }).toPromise();
      this.workOrder.set(updated ?? null);
      this.showProgressDialog.set(false);
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Progress recorded',
      });
    } catch (error: any) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: error.error?.detail || 'Failed to record progress',
      });
    }
  }

  // Build dialog
  openBuildDialog(): void {
    this.buildQuantity = 1;
    this.buildNotes = '';
    this.showBuildDialog.set(true);
  }

  async performBuild(): Promise<void> {
    const wo = this.workOrder();
    if (!wo) return;
    
    try {
      const updated = await this.workOrderService.buildFromWorkOrder(wo.id, {
        quantity: this.buildQuantity,
        notes: this.buildNotes,
      }).toPromise();
      this.workOrder.set(updated ?? null);
      this.showBuildDialog.set(false);
      
      // Refresh BOM availability
      if (wo.itemId) {
        this.loadBomData(wo.itemId);
      }
      
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: `Built ${this.buildQuantity} assemblies`,
      });
    } catch (error: any) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: error.error?.detail || 'Failed to build assemblies',
      });
    }
  }

  // Delete
  confirmDelete(): void {
    const wo = this.workOrder();
    if (!wo) return;
    
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
          this.router.navigate(['/work-orders']);
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

  canDelete(): boolean {
    const wo = this.workOrder();
    return wo !== null && [WorkOrderStatus.DRAFT, WorkOrderStatus.CANCELLED].includes(wo.status);
  }

  getProgressColor(): string {
    const wo = this.workOrder();
    if (!wo) return '#64748B';
    if ((wo.completionPercentage ?? 0) >= 100) return '#10B981';
    if (wo.isOverdue) return '#EF4444';
    if ((wo.completionPercentage ?? 0) > 50) return '#0D9488';
    return '#F59E0B';
  }

  viewItem(): void {
    const wo = this.workOrder();
    if (wo?.itemId) {
      this.router.navigate(['/inventory', wo.itemId], { queryParams: { tab: 'bom' } });
    }
  }
}
