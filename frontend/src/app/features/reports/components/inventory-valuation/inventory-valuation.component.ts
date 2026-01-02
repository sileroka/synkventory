import { Component, OnInit } from '@angular/core';
import { CommonModule, CurrencyPipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { MultiSelectModule } from 'primeng/multiselect';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { TabViewModule } from 'primeng/tabview';
import { MessageService } from 'primeng/api';
import { ReportService } from '../../services/report.service';
import { LocationService } from '../../../locations/services/location.service';
import { CategoryService } from '../../../categories/services/category.service';
import {
  IInventoryValuationReport,
  IValuationItem,
  ICategoryValuationSummary,
  ILocationValuationSummary
} from '../../models/report.model';
import { ILocation } from '../../../locations/models/location.model';
import { ICategory } from '../../../categories/models/category.model';

interface IFilterOption {
  label: string;
  value: string;
}

@Component({
  selector: 'app-inventory-valuation',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    TableModule,
    ButtonModule,
    MultiSelectModule,
    ProgressSpinnerModule,
    ToastModule,
    TooltipModule,
    TabViewModule
  ],
  providers: [MessageService, CurrencyPipe, DecimalPipe],
  templateUrl: './inventory-valuation.component.html',
  styleUrls: ['./inventory-valuation.component.scss']
})
export class InventoryValuationComponent implements OnInit {
  // Report data
  report: IInventoryValuationReport | null = null;
  loading = false;

  // Filter options
  categoryOptions: IFilterOption[] = [];
  locationOptions: IFilterOption[] = [];
  selectedCategories: string[] = [];
  selectedLocations: string[] = [];

  constructor(
    private reportService: ReportService,
    private locationService: LocationService,
    private categoryService: CategoryService,
    private messageService: MessageService,
    private currencyPipe: CurrencyPipe,
    private decimalPipe: DecimalPipe
  ) {}

  ngOnInit() {
    this.loadFilterOptions();
    this.loadReport();
  }

  loadFilterOptions() {
    // Load categories
    this.categoryService.getCategories(1, 100).subscribe({
      next: (result: { items: ICategory[]; pagination: unknown }) => {
        this.categoryOptions = result.items.map((cat: ICategory) => ({
          label: cat.name,
          value: cat.id!
        }));
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load categories'
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
    this.reportService
      .getInventoryValuation(
        this.selectedCategories.length > 0 ? this.selectedCategories : undefined,
        this.selectedLocations.length > 0 ? this.selectedLocations : undefined
      )
      .subscribe({
        next: (report: IInventoryValuationReport) => {
          this.report = report;
          this.loading = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to load valuation report'
          });
          this.loading = false;
        }
      });
  }

  onFilterChange() {
    this.loadReport();
  }

  clearFilters() {
    this.selectedCategories = [];
    this.selectedLocations = [];
    this.loadReport();
  }

  exportToCsv() {
    if (!this.report || this.report.items.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Data',
        detail: 'No data to export'
      });
      return;
    }

    // Build CSV content
    const headers = [
      'SKU',
      'Name',
      'Category',
      'Location',
      'Quantity',
      'Unit Price',
      'Total Value'
    ];

    const rows = this.report.items.map((item: IValuationItem) => [
      this.escapeCsvField(item.sku),
      this.escapeCsvField(item.name),
      this.escapeCsvField(item.category?.name || 'Uncategorized'),
      this.escapeCsvField(item.location?.name || 'Unassigned'),
      item.quantity.toString(),
      item.unitPrice.toFixed(2),
      item.totalValue.toFixed(2)
    ]);

    // Add summary rows
    rows.push([]);
    rows.push(['Summary', '', '', '', '', '', '']);
    rows.push(['Total Items', this.report.totalItems.toString(), '', '', '', '', '']);
    rows.push(['Total Units', this.report.totalUnits.toString(), '', '', '', '', '']);
    rows.push(['Total Value', '', '', '', '', '', this.report.totalValue.toFixed(2)]);

    // Add category breakdown
    rows.push([]);
    rows.push(['By Category', '', '', '', 'Items', 'Units', 'Value']);
    this.report.byCategory.forEach((cat: ICategoryValuationSummary) => {
      rows.push([
        cat.categoryName,
        '',
        '',
        '',
        cat.itemCount.toString(),
        cat.totalUnits.toString(),
        cat.totalValue.toFixed(2)
      ]);
    });

    // Add location breakdown
    rows.push([]);
    rows.push(['By Location', '', '', '', 'Items', 'Units', 'Value']);
    this.report.byLocation.forEach((loc: ILocationValuationSummary) => {
      rows.push([
        loc.locationName,
        '',
        '',
        '',
        loc.itemCount.toString(),
        loc.totalUnits.toString(),
        loc.totalValue.toFixed(2)
      ]);
    });

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
      `inventory-valuation-${new Date().toISOString().split('T')[0]}.csv`
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

  formatCurrency(value: number): string {
    return this.currencyPipe.transform(value, 'USD', 'symbol', '1.2-2') || '$0.00';
  }

  formatNumber(value: number): string {
    return this.decimalPipe.transform(value, '1.0-0') || '0';
  }
}
