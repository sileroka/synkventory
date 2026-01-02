import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { CalendarModule } from 'primeng/calendar';
import { MultiSelectModule } from 'primeng/multiselect';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { MessageService } from 'primeng/api';
import { ReportService } from '../../services/report.service';
import { InventoryService } from '../../../../services/inventory.service';
import { LocationService } from '../../../locations/services/location.service';
import {
  IStockMovementReport,
  IStockMovementReportEntry,
  MovementType
} from '../../models/report.model';
import { IInventoryItem } from '../../../../models/inventory-item.model';
import { ILocation } from '../../../locations/models/location.model';

interface IFilterOption {
  label: string;
  value: string;
}

interface IMovementTypeOption {
  label: string;
  value: MovementType;
}

@Component({
  selector: 'app-stock-movement-report',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    CalendarModule,
    MultiSelectModule,
    ProgressSpinnerModule,
    ToastModule,
    TooltipModule,
    TagModule
  ],
  providers: [MessageService, DatePipe, DecimalPipe],
  templateUrl: './stock-movement-report.component.html',
  styleUrls: ['./stock-movement-report.component.scss']
})
export class StockMovementReportComponent implements OnInit {
  // Report data
  report: IStockMovementReport | null = null;
  loading = false;

  // Date range
  dateRange: Date[] = [];
  maxDate: Date = new Date();

  // Filter options
  itemOptions: IFilterOption[] = [];
  locationOptions: IFilterOption[] = [];
  movementTypeOptions: IMovementTypeOption[] = [
    { label: 'Receive', value: 'receive' },
    { label: 'Ship', value: 'ship' },
    { label: 'Transfer', value: 'transfer' },
    { label: 'Adjust', value: 'adjust' },
    { label: 'Count', value: 'count' }
  ];

  // Selected filters
  selectedItems: string[] = [];
  selectedLocations: string[] = [];
  selectedMovementTypes: MovementType[] = [];

  constructor(
    private reportService: ReportService,
    private inventoryService: InventoryService,
    private locationService: LocationService,
    private messageService: MessageService,
    private datePipe: DatePipe,
    private decimalPipe: DecimalPipe
  ) {}

  ngOnInit() {
    // Set default date range to last 30 days
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    this.dateRange = [startDate, endDate];

    this.loadFilterOptions();
    this.loadReport();
  }

  loadFilterOptions() {
    // Load inventory items
    this.inventoryService.getItems(1, 500).subscribe({
      next: (result: { items: IInventoryItem[]; pagination: unknown }) => {
        this.itemOptions = result.items.map((item: IInventoryItem) => ({
          label: `${item.sku} - ${item.name}`,
          value: item.id!
        }));
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load inventory items'
        });
      }
    });

    // Load locations
    this.locationService.getLocations(1, 100, true).subscribe({
      next: (result: { items: ILocation[]; pagination: unknown }) => {
        this.locationOptions = result.items.map((loc: ILocation) => ({
          label: loc.name,
          value: loc.id!
        }));
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load locations'
        });
      }
    });
  }

  loadReport() {
    this.loading = true;

    const startDate = this.dateRange[0] || undefined;
    const endDate = this.dateRange[1] || undefined;

    this.reportService
      .getStockMovementReport(
        startDate,
        endDate,
        this.selectedItems.length > 0 ? this.selectedItems : undefined,
        this.selectedLocations.length > 0 ? this.selectedLocations : undefined,
        this.selectedMovementTypes.length > 0 ? this.selectedMovementTypes : undefined
      )
      .subscribe({
        next: (report: IStockMovementReport) => {
          this.report = report;
          this.loading = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to load stock movement report'
          });
          this.loading = false;
        }
      });
  }

  onFilterChange() {
    this.loadReport();
  }

  clearFilters() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    this.dateRange = [startDate, endDate];
    this.selectedItems = [];
    this.selectedLocations = [];
    this.selectedMovementTypes = [];
    this.loadReport();
  }

  exportToCsv() {
    if (!this.report || this.report.movements.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Data',
        detail: 'No data to export'
      });
      return;
    }

    // Build CSV content
    const headers = [
      'Date',
      'SKU',
      'Item Name',
      'Type',
      'Quantity',
      'From Location',
      'To Location',
      'Reference',
      'Notes',
      'Running Balance'
    ];

    const rows = this.report.movements.map((m: IStockMovementReportEntry) => [
      this.formatDateForCsv(m.date),
      this.escapeCsvField(m.inventoryItem.sku),
      this.escapeCsvField(m.inventoryItem.name),
      this.getMovementTypeLabel(m.movementType),
      m.quantity.toString(),
      m.fromLocation?.name || '',
      m.toLocation?.name || '',
      m.referenceNumber || '',
      this.escapeCsvField(m.notes || ''),
      m.runningBalance.toString()
    ]);

    // Add summary rows
    rows.push([]);
    rows.push(['Summary', '', '', '', '', '', '', '', '', '']);
    rows.push([
      'Total Movements',
      this.report.summary.totalMovements.toString(),
      '',
      '',
      '',
      '',
      '',
      '',
      '',
      ''
    ]);
    rows.push([
      'Total In',
      this.report.summary.totalIn.toString(),
      '',
      '',
      '',
      '',
      '',
      '',
      '',
      ''
    ]);
    rows.push([
      'Total Out',
      this.report.summary.totalOut.toString(),
      '',
      '',
      '',
      '',
      '',
      '',
      '',
      ''
    ]);
    rows.push([
      'Net Change',
      this.report.summary.netChange.toString(),
      '',
      '',
      '',
      '',
      '',
      '',
      '',
      ''
    ]);

    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join(
      '\n'
    );

    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute(
      'download',
      `stock-movements-${new Date().toISOString().split('T')[0]}.csv`
    );
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    this.messageService.add({
      severity: 'success',
      summary: 'Exported',
      detail: 'Report exported to CSV'
    });
  }

  private escapeCsvField(field: string): string {
    if (field.includes(',') || field.includes('"') || field.includes('\n')) {
      return `"${field.replace(/"/g, '""')}"`;
    }
    return field;
  }

  private formatDateForCsv(dateStr: string): string {
    const date = new Date(dateStr);
    return this.datePipe.transform(date, 'yyyy-MM-dd HH:mm:ss') || '';
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return this.datePipe.transform(date, 'MMM d, y h:mm a') || '';
  }

  formatNumber(value: number): string {
    return this.decimalPipe.transform(value, '1.0-0') || '0';
  }

  getMovementTypeLabel(type: MovementType): string {
    const labels: Record<MovementType, string> = {
      receive: 'Receive',
      ship: 'Ship',
      transfer: 'Transfer',
      adjust: 'Adjust',
      count: 'Count'
    };
    return labels[type] || type;
  }

  getMovementTypeSeverity(type: MovementType): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
    const severities: Record<MovementType, 'success' | 'info' | 'warn' | 'danger' | 'secondary'> = {
      receive: 'success',
      ship: 'danger',
      transfer: 'info',
      adjust: 'warn',
      count: 'secondary'
    };
    return severities[type] || 'secondary';
  }

  getQuantityClass(quantity: number): string {
    return quantity >= 0 ? 'quantity-positive' : 'quantity-negative';
  }
}
