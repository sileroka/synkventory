import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { TableModule, TableLazyLoadEvent } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TagModule } from 'primeng/tag';
import { DropdownModule } from 'primeng/dropdown';
import { MultiSelectModule } from 'primeng/multiselect';
import { TooltipModule } from 'primeng/tooltip';
import { ToolbarModule } from 'primeng/toolbar';
import { FileUploadModule } from 'primeng/fileupload';
import { ImageModule } from 'primeng/image';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageService, ConfirmationService } from 'primeng/api';
import { InventoryService, IInventoryFilters } from '../../services/inventory.service';
import { LocationService } from '../../features/locations/services/location.service';
import { CategoryService } from '../../features/categories/services/category.service';
import { UploadService } from '../../services/upload.service';
import { IInventoryItem, IInventoryLocationQuantity, InventoryStatus } from '../../models/inventory-item.model';
import { ILocation } from '../../features/locations/models/location.model';
import { ICategory } from '../../features/categories/models/category.model';

interface ISelectOption {
  label: string;
  value: string | null;
}

interface IMultiSelectOption {
  label: string;
  value: string;
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
    DropdownModule,
    MultiSelectModule,
    TooltipModule,
    ToolbarModule,
    FileUploadModule,
    ImageModule,
    ProgressSpinnerModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './inventory-list.component.html',
  styleUrl: './inventory-list.component.scss'
})
export class InventoryListComponent implements OnInit {
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  items: IInventoryItem[] = [];
  displayDialog: boolean = false;
  displayDetailDialog: boolean = false;
  displayQuickAdjustDialog: boolean = false;
  selectedItem: IInventoryItem = this.getEmptyItem();
  detailItem: IInventoryItem | null = null;
  quickAdjustItem: IInventoryItem | null = null;
  quickAdjustQuantity: number = 0;
  quickAdjustReason: string = '';
  locationQuantities: IInventoryLocationQuantity[] = [];
  isEditMode: boolean = false;
  loading: boolean = false;
  loadingDetail: boolean = false;
  uploadingImage: boolean = false;
  selectedImageFile: File | null = null;
  imagePreviewUrl: string | null = null;

  // Selection for bulk actions
  selectedItems: IInventoryItem[] = [];

  // Pagination
  totalRecords: number = 0;
  currentPage: number = 1;
  pageSize: number = 25;

  // Filters
  searchTerm: string = '';
  selectedCategories: string[] = [];
  selectedLocations: string[] = [];
  selectedStatuses: string[] = [];

  // Sorting
  sortField: string = '';
  sortOrder: number = 1;

  // Dropdown options
  locationOptions: ISelectOption[] = [];
  categoryOptions: ISelectOption[] = [];
  locationMultiOptions: IMultiSelectOption[] = [];
  categoryMultiOptions: IMultiSelectOption[] = [];

  statusOptions = [
    { label: 'In Stock', value: InventoryStatus.IN_STOCK },
    { label: 'Low Stock', value: InventoryStatus.LOW_STOCK },
    { label: 'Out of Stock', value: InventoryStatus.OUT_OF_STOCK },
    { label: 'On Order', value: InventoryStatus.ON_ORDER },
    { label: 'Discontinued', value: InventoryStatus.DISCONTINUED }
  ];

  statusMultiOptions: IMultiSelectOption[] = [
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
    private uploadService: UploadService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadItems();
    this.loadLocations();
    this.loadCategories();
  }

  loadItems() {
    this.loading = true;
    const filters: IInventoryFilters = {
      search: this.searchTerm || undefined,
      categoryIds: this.selectedCategories.length > 0 ? this.selectedCategories : undefined,
      locationIds: this.selectedLocations.length > 0 ? this.selectedLocations : undefined,
      statuses: this.selectedStatuses.length > 0 ? this.selectedStatuses : undefined,
      sortField: this.sortField || undefined,
      sortOrder: this.sortField ? this.sortOrder : undefined
    };

    this.inventoryService.getItems(this.currentPage, this.pageSize, filters).subscribe({
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
        this.locationMultiOptions = result.items.map((loc: ILocation) => ({
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
        this.categoryMultiOptions = result.items.map((cat: ICategory) => ({
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
  }

  onLazyLoad(event: TableLazyLoadEvent) {
    this.currentPage = Math.floor((event.first || 0) / (event.rows || this.pageSize)) + 1;
    this.pageSize = event.rows || this.pageSize;

    if (event.sortField && typeof event.sortField === 'string') {
      this.sortField = event.sortField;
      this.sortOrder = event.sortOrder || 1;
    }

    this.loadItems();
  }

  onPageChange(event: { first: number; rows: number }) {
    this.currentPage = Math.floor(event.first / event.rows) + 1;
    this.pageSize = event.rows;
    this.loadItems();
  }

  // Filter methods
  onSearch() {
    this.currentPage = 1;
    this.loadItems();
  }

  onFilterChange() {
    this.currentPage = 1;
    this.loadItems();
  }

  clearFilters() {
    this.searchTerm = '';
    this.selectedCategories = [];
    this.selectedLocations = [];
    this.selectedStatuses = [];
    this.currentPage = 1;
    this.loadItems();
  }

  hasActiveFilters(): boolean {
    return !!(
      this.searchTerm ||
      this.selectedCategories.length > 0 ||
      this.selectedLocations.length > 0 ||
      this.selectedStatuses.length > 0
    );
  }

  // Bulk actions
  bulkDelete() {
    if (this.selectedItems.length === 0) return;

    this.confirmationService.confirm({
      message: `Are you sure you want to delete ${this.selectedItems.length} item(s)?`,
      header: 'Confirm Bulk Delete',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        const ids = this.selectedItems.map(item => item.id!);
        this.inventoryService.bulkDelete(ids).subscribe({
          next: (result) => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: `Deleted ${result.successCount} item(s)${result.failedCount > 0 ? `, ${result.failedCount} failed` : ''}`
            });
            this.selectedItems = [];
            this.loadItems();
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete items'
            });
          }
        });
      }
    });
  }

  bulkStatusChange(status: InventoryStatus | string) {
    if (this.selectedItems.length === 0) return;

    const statusEnum = status as InventoryStatus;
    const ids = this.selectedItems.map(item => item.id!);
    this.inventoryService.bulkStatusUpdate(ids, statusEnum).subscribe({
      next: (result) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Updated ${result.successCount} item(s) to ${this.getStatusLabel(statusEnum)}`
        });
        this.selectedItems = [];
        this.loadItems();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to update items'
        });
      }
    });
  }

  exportSelectedToCsv() {
    if (this.selectedItems.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Warning',
        detail: 'Please select items to export'
      });
      return;
    }

    const headers = ['SKU', 'Name', 'Description', 'Quantity', 'Reorder Point', 'Status', 'Unit Price', 'Category', 'Location'];
    const rows = this.selectedItems.map(item => [
      item.sku,
      item.name,
      item.description || '',
      item.quantity.toString(),
      item.reorderPoint.toString(),
      this.getStatusLabel(item.status),
      item.unitPrice.toString(),
      item.category?.name || '',
      item.location?.name || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `inventory-export-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: `Exported ${this.selectedItems.length} item(s) to CSV`
    });
  }

  // Quick Adjust
  showQuickAdjustDialog(item: IInventoryItem) {
    this.quickAdjustItem = item;
    this.quickAdjustQuantity = item.quantity;
    this.quickAdjustReason = '';
    this.displayQuickAdjustDialog = true;
  }

  saveQuickAdjust() {
    if (!this.quickAdjustItem?.id) return;

    this.inventoryService.quickAdjust(
      this.quickAdjustItem.id,
      this.quickAdjustQuantity,
      this.quickAdjustReason || undefined
    ).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Quantity adjusted successfully'
        });
        this.displayQuickAdjustDialog = false;
        this.loadItems();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to adjust quantity'
        });
      }
    });
  }

  showAddDialog() {
    this.selectedItem = this.getEmptyItem();
    this.isEditMode = false;
    this.selectedImageFile = null;
    this.imagePreviewUrl = null;
    this.displayDialog = true;
  }

  showEditDialog(item: IInventoryItem) {
    this.selectedItem = {
      ...item,
      categoryId: item.category?.id || item.categoryId || null,
      locationId: item.location?.id || item.locationId || null
    };
    this.isEditMode = true;
    this.selectedImageFile = null;
    this.imagePreviewUrl = item.imageUrl || null;
    this.displayDialog = true;
  }

  onImageSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];

      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        this.messageService.add({
          severity: 'error',
          summary: 'Invalid File',
          detail: 'Please select a valid image (JPEG, PNG, GIF, or WebP)'
        });
        return;
      }

      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        this.messageService.add({
          severity: 'error',
          summary: 'File Too Large',
          detail: 'Image must be less than 10MB'
        });
        return;
      }

      this.selectedImageFile = file;

      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        this.imagePreviewUrl = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    }
  }

  triggerFileInput() {
    this.fileInput?.nativeElement?.click();
  }

  removeImage() {
    this.selectedImageFile = null;
    this.imagePreviewUrl = null;
    if (this.fileInput?.nativeElement) {
      this.fileInput.nativeElement.value = '';
    }
  }

  private uploadImageIfNeeded(itemId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.selectedImageFile) {
        resolve();
        return;
      }

      this.uploadingImage = true;
      this.uploadService.uploadInventoryImage(itemId, this.selectedImageFile).subscribe({
        next: () => {
          this.uploadingImage = false;
          resolve();
        },
        error: (err) => {
          this.uploadingImage = false;
          this.messageService.add({
            severity: 'warn',
            summary: 'Image Upload Failed',
            detail: 'Item was saved but image upload failed'
          });
          resolve(); // Don't reject - item was still saved
        }
      });
    });
  }

  saveItem() {
    if (this.isEditMode && this.selectedItem.id) {
      this.inventoryService.updateItem(this.selectedItem.id, this.selectedItem).subscribe({
        next: async () => {
          await this.uploadImageIfNeeded(this.selectedItem.id!);
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
        next: async (createdItem) => {
          if (createdItem.id && this.selectedImageFile) {
            await this.uploadImageIfNeeded(createdItem.id);
          }
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

  getRowClass(item: IInventoryItem): string {
    switch (item.status) {
      case InventoryStatus.OUT_OF_STOCK:
        return 'row-out-of-stock';
      case InventoryStatus.LOW_STOCK:
        return 'row-low-stock';
      case InventoryStatus.DISCONTINUED:
        return 'row-discontinued';
      case InventoryStatus.ON_ORDER:
        return 'row-on-order';
      default:
        return 'row-in-stock';
    }
  }

  viewItemDetail(item: IInventoryItem) {
    if (item.id) {
      this.router.navigate(['/inventory', item.id]);
    }
  }

  showDetailDialog(item: IInventoryItem) {
    this.detailItem = item;
    this.locationQuantities = [];
    this.displayDetailDialog = true;
    this.loadingDetail = true;

    if (item.id) {
      this.inventoryService.getItemLocationQuantities(item.id).subscribe({
        next: (result) => {
          this.locationQuantities = result.items;
          this.loadingDetail = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to load location quantities'
          });
          this.loadingDetail = false;
        }
      });
    }
  }
}
