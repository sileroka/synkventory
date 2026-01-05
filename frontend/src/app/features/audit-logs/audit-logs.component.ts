import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { CardModule } from 'primeng/card';
import { MessageService } from 'primeng/api';
import {
  AuditLogService,
  IAuditLog,
  IAuditLogFilters,
  ActionLabels,
} from '../../services/audit-log.service';

interface DropdownOption {
  label: string;
  value: string;
}

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    CalendarModule,
    TagModule,
    TooltipModule,
    ToastModule,
    DialogModule,
    CardModule,
  ],
  providers: [MessageService],
  templateUrl: './audit-logs.component.html',
  styleUrl: './audit-logs.component.scss',
})
export class AuditLogsComponent implements OnInit {
  private auditService = inject(AuditLogService);
  private messageService = inject(MessageService);

  // Data
  logs = signal<IAuditLog[]>([]);
  isLoading = signal(true);

  // Pagination
  page = signal(1);
  pageSize = signal(50);
  totalItems = signal(0);
  totalPages = signal(1);

  // Filter options
  actions = signal<DropdownOption[]>([]);
  entityTypes = signal<DropdownOption[]>([]);

  // Current filters
  filters: IAuditLogFilters = {};
  dateRange: Date[] | null = null;
  searchText = '';

  // Detail dialog
  showDetailDialog = signal(false);
  selectedLog = signal<IAuditLog | null>(null);

  // Action labels for UI
  actionLabels = ActionLabels;

  ngOnInit(): void {
    this.loadFilterOptions();
    this.loadLogs();
  }

  loadFilterOptions(): void {
    // Load actions
    this.auditService.getActions().subscribe({
      next: (actions) => {
        this.actions.set([
          { label: 'All Actions', value: '' },
          ...actions.map((a) => ({ label: this.actionLabels[a] || a, value: a })),
        ]);
      },
    });

    // Load entity types
    this.auditService.getEntityTypes().subscribe({
      next: (types) => {
        this.entityTypes.set([
          { label: 'All Types', value: '' },
          ...types.map((t) => ({ label: this.formatEntityType(t), value: t })),
        ]);
      },
    });
  }

  loadLogs(): void {
    this.isLoading.set(true);

    this.auditService.getAuditLogs(this.page(), this.pageSize(), this.filters).subscribe({
      next: (response) => {
        this.logs.set(response.data);
        this.totalItems.set(response.meta.totalItems);
        this.totalPages.set(response.meta.totalPages);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load audit logs',
        });
        this.isLoading.set(false);
      },
    });
  }

  onPageChange(event: any): void {
    this.page.set(Math.floor(event.first / event.rows) + 1);
    this.pageSize.set(event.rows);
    this.loadLogs();
  }

  onFilterChange(): void {
    this.page.set(1);
    this.loadLogs();
  }

  onSearch(): void {
    this.filters.search = this.searchText || undefined;
    this.onFilterChange();
  }

  onDateRangeChange(): void {
    if (this.dateRange && this.dateRange.length === 2 && this.dateRange[0] && this.dateRange[1]) {
      this.filters.startDate = this.formatDate(this.dateRange[0]);
      this.filters.endDate = this.formatDate(this.dateRange[1]);
    } else {
      this.filters.startDate = undefined;
      this.filters.endDate = undefined;
    }
    this.onFilterChange();
  }

  clearFilters(): void {
    this.filters = {};
    this.dateRange = null;
    this.searchText = '';
    this.onFilterChange();
  }

  showDetails(log: IAuditLog): void {
    this.selectedLog.set(log);
    this.showDetailDialog.set(true);
  }

  // Formatting helpers
  formatDateTime(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  formatEntityType(type: string): string {
    return type
      .split('_')
      .map((word) => word.charAt(0) + word.slice(1).toLowerCase())
      .join(' ');
  }

  getActionLabel(action: string): string {
    return this.actionLabels[action] || action;
  }

  getActionSeverity(action: string): 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast' {
    const severityMap: Record<string, 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast'> = {
      LOGIN: 'success',
      LOGOUT: 'secondary',
      LOGIN_FAILED: 'danger',
      CREATE: 'success',
      UPDATE: 'info',
      DELETE: 'danger',
      STOCK_RECEIVE: 'success',
      STOCK_SHIP: 'info',
      STOCK_TRANSFER: 'info',
      STOCK_ADJUST: 'warning',
      BULK_DELETE: 'danger',
      BULK_UPDATE: 'warning',
      BULK_IMPORT: 'info',
      WORK_ORDER_CREATE: 'info',
      WORK_ORDER_START: 'info',
      WORK_ORDER_COMPLETE: 'success',
      WORK_ORDER_CANCEL: 'danger',
      PURCHASE_ORDER_CREATE: 'info',
      PURCHASE_ORDER_SUBMIT: 'info',
      PURCHASE_ORDER_APPROVE: 'success',
      PURCHASE_ORDER_RECEIVE: 'success',
      PURCHASE_ORDER_CANCEL: 'danger',
    };
    return severityMap[action] || 'secondary';
  }

  formatExtraData(data: Record<string, unknown> | undefined): string {
    if (!data) return '';
    return JSON.stringify(data, null, 2);
  }
}
