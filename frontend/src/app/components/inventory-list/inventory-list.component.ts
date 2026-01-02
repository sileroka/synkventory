import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TagModule } from 'primeng/tag';
import { SelectModule } from 'primeng/select';
import { MessageService, ConfirmationService } from 'primeng/api';
import { InventoryService } from '../../services/inventory.service';
import { LocationService } from '../../features/locations/services/location.service';
import { CategoryService } from '../../features/categories/services/category.service';
import { IInventoryItem, InventoryStatus } from '../../models/inventory-item.model';
import { ILocation } from '../../features/locations/models/location.model';
import { ICategory } from '../../features/categories/models/category.model';

interface ISelectOption {
  label: string;
  value: string | null;
}

@Component({
  selector: 'app-inventory-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputNumberModule,
    InputTextareaModule,
    ToastModule,
    ConfirmDialogModule,
    TagModule,
    SelectModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './inventory-list.component.html',
  styleUrl: './inventory-list.component.scss'
})
export class InventoryListComponent implements OnInit {
  items: IInventoryItem[] = [];
  displayDialog: boolean = false;
  selectedItem: IInventoryItem = this.getEmptyItem();
  isEditMode: boolean = false;
  loading: boolean = false;

  // Pagination
  totalRecords: number = 0;
  currentPage: number = 1;
  pageSize: number = 25;

  // Dropdown options
  locationOptions: ISelectOption[] = [];
  categoryOptions: ISelectOption[] = [];

  statusOptions = [
    { label: 'In Stock', value: InventoryStatus.IN_STOCK },
    { label: 'Low Stock', value: InventoryStatus.LOW_STOCK },
    { label: 'Out of Stock', value: InventoryStatus.OUT_OF_STOCK },
    { label: 'On Order', value: InventoryStatus.ON_ORDER },
    { label: 'Discontinued', value: InventoryStatus.DISCONTINUED }
  ];

  constructor(
    private inventoryService: InventoryService,
    private locationService: LocationService,
    private categoryService: CategoryService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.loadItems();
    this.loadLocations();
    this.loadCategories();
  }

  loadItems() {
    this.loading = true;
    this.inventoryService.getItems(this.currentPage, this.pageSize).subscribe({
      next: (result) => {
        this.items = result.items;
        this.totalRecords = result.pagination.totalItems;
        this.loading = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load inventory items'
        });
        this.loading = false;
      }
    });
  }

  loadLocations() {
    this.locationService.getLocations(1, 100, true).subscribe({
      next: (result) => {
        this.locationOptions = [
          { label: 'None', value: null },
          ...result.items.map((loc: ILocation) => ({
            label: loc.name,
            value: loc.id!
          }))
        ];
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

  loadCategories() {
    this.categoryService.getCategories(1, 100, true).subscribe({
      next: (result) => {
        this.categoryOptions = [
          { label: 'None', value: null },
          ...result.items.map((cat: ICategory) => ({
            label: cat.name,
            value: cat.id!
          }))
        ];
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load categories'
        });
      }
    });
  }

  onPageChange(event: { first: number; rows: number }) {
    this.currentPage = Math.floor(event.first / event.rows) + 1;
    this.pageSize = event.rows;
    this.loadItems();
  }

  showAddDialog() {
    this.selectedItem = this.getEmptyItem();
    this.isEditMode = false;
    this.displayDialog = true;
  }

  showEditDialog(item: IInventoryItem) {
    this.selectedItem = {
      ...item,
      categoryId: item.category?.id || item.categoryId || null,
      locationId: item.location?.id || item.locationId || null
    };
    this.isEditMode = true;
    this.displayDialog = true;
  }

  saveItem() {
    if (this.isEditMode && this.selectedItem.id) {
      this.inventoryService.updateItem(this.selectedItem.id, this.selectedItem).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Item updated successfully'
          });
          this.loadItems();
          this.displayDialog = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to update item'
          });
        }
      });
    } else {
      this.inventoryService.createItem(this.selectedItem).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Item created successfully'
          });
          this.loadItems();
          this.displayDialog = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create item'
          });
        }
      });
    }
  }

  deleteItem(item: IInventoryItem) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete ${item.name}?`,
      accept: () => {
        if (item.id) {
          this.inventoryService.deleteItem(item.id).subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Item deleted successfully'
              });
              this.loadItems();
            },
            error: () => {
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to delete item'
              });
            }
          });
        }
      }
    });
  }

  getEmptyItem(): IInventoryItem {
    return {
      name: '',
      sku: '',
      description: '',
      quantity: 0,
      reorderPoint: 0,
      unitPrice: 0,
      status: InventoryStatus.IN_STOCK,
      categoryId: null,
      locationId: null
    };
  }

  getStatusLabel(status: InventoryStatus): string {
    const labels: Record<InventoryStatus, string> = {
      [InventoryStatus.IN_STOCK]: 'In Stock',
      [InventoryStatus.LOW_STOCK]: 'Low Stock',
      [InventoryStatus.OUT_OF_STOCK]: 'Out of Stock',
      [InventoryStatus.ON_ORDER]: 'On Order',
      [InventoryStatus.DISCONTINUED]: 'Discontinued'
    };
    return labels[status] || status;
  }
}
