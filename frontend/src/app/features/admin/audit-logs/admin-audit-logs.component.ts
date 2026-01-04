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
import { MessageService } from 'primeng/api';
import { AdminAuditService } from './services/admin-audit.service';
import { AdminApiService, Tenant } from '../../../core/services/admin-api.service';
import { IAuditLog, IAuditLogFilters, ActionLabels } from './models/audit-log.model';

interface DropdownOption {
  label: string;
  value: string;
}

@Component({
  selector: 'app-admin-audit-logs',
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
  ],
  providers: [MessageService],
  templateUrl: './admin-audit-logs.component.html',
  styleUrl: './admin-audit-logs.component.scss'
})
export class AdminAuditLogsComponent implements OnInit {
  private auditService = inject(AdminAuditService);
  private adminApiService = inject(AdminApiService);
  private messageService = inject(MessageService);

  // Data
  logs = signal<IAuditLog[]>([]);
  tenants = signal<Tenant[]>([]);
  isLoading = signal(true);

  // Pagination
  page = signal(1);
  pageSize = signal(50);
  totalItems = signal(0);
  totalPages = signal(1);

  // Filter options
  actions = signal<DropdownOption[]>([]);
  entityTypes = signal<DropdownOption[]>([]);
  tenantOptions = signal<DropdownOption[]>([]);

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
    // Load tenants
    this.adminApiService.getTenants().subscribe({
      next: (tenants) => {
        this.tenants.set(tenants);
        this.tenantOptions.set([
          { label: 'All Tenants', value: '' },
          ...tenants.map(t => ({ label: t.name, value: t.id }))
        ]);
      }
    });

    // Load actions
    this.auditService.getActions().subscribe({
      next: (actions) => {
        this.actions.set([
          { label: 'All Actions', value: '' },
          ...actions.map(a => ({ label: this.actionLabels[a] || a, value: a }))
        ]);
      }
    });

    // Load entity types
    this.auditService.getEntityTypes().subscribe({
      next: (types) => {
        this.entityTypes.set([
          { label: 'All Types', value: '' },
          ...types.map(t => ({ label: t.replace(/_/g, ' '), value: t }))
        ]);
      }
    });
  }

  loadLogs(): void {
    this.isLoading.set(true);

    // Build filters from current state
    const activeFilters: IAuditLogFilters = { ...this.filters };
    if (this.searchText) {
      activeFilters.search = this.searchText;
    }
    if (this.dateRange && this.dateRange[0]) {
      activeFilters.startDate = this.formatDate(this.dateRange[0]);
    }
    if (this.dateRange && this.dateRange[1]) {
      activeFilters.endDate = this.formatDate(this.dateRange[1]);
    }

    this.auditService.getAuditLogs(this.page(), this.pageSize(), activeFilters).subscribe({
      next: (response) => {
        this.logs.set(response.data);
        this.totalItems.set(response.meta.totalItems);
        this.totalPages.set(response.meta.totalPages);
        this.isLoading.set(false);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load audit logs'
        });
        this.isLoading.set(false);
      }
    });
  }

  onFilterChange(): void {
    this.page.set(1); // Reset to first page
    this.loadLogs();
  }

  onSearch(): void {
    this.page.set(1);
    this.loadLogs();
  }

  onDateRangeChange(): void {
    this.page.set(1);
    this.loadLogs();
  }

  clearFilters(): void {
    this.filters = {};
    this.searchText = '';
    this.dateRange = null;
    this.page.set(1);
    this.loadLogs();
  }

  onPageChange(event: any): void {
    this.page.set(event.first / event.rows + 1);
    this.pageSize.set(event.rows);
    this.loadLogs();
  }

  showDetails(log: IAuditLog): void {
    this.selectedLog.set(log);
    this.showDetailDialog.set(true);
  }

  getActionSeverity(action: string): 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast' {
    switch (action) {
      case 'LOGIN':
        return 'success';
      case 'LOGOUT':
        return 'secondary';
      case 'LOGIN_FAILED':
        return 'danger';
      case 'CREATE':
        return 'success';
      case 'UPDATE':
        return 'info';
      case 'DELETE':
      case 'BULK_DELETE':
        return 'danger';
      case 'PAGE_VIEW':
        return 'secondary';
      default:
        return 'info';
    }
  }

  getActionLabel(action: string): string {
    return this.actionLabels[action] || action;
  }

  formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  formatDateTime(dateStr: string): string {
    return new Date(dateStr).toLocaleString();
  }

  parseUserAgent(ua?: string): string {
    if (!ua) return 'Unknown';

    // Simple browser detection
    if (ua.includes('Chrome')) return 'Chrome';
    if (ua.includes('Firefox')) return 'Firefox';
    if (ua.includes('Safari')) return 'Safari';
    if (ua.includes('Edge')) return 'Edge';
    return 'Other';
  }
}
