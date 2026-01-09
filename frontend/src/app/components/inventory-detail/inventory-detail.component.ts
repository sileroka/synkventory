import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TableModule } from 'primeng/table';
import { TimelineModule } from 'primeng/timeline';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { BreadcrumbModule } from 'primeng/breadcrumb';
import { TooltipModule } from 'primeng/tooltip';
import { SkeletonModule } from 'primeng/skeleton';
import { TabViewModule } from 'primeng/tabview';
import { MessageService, ConfirmationService, MenuItem } from 'primeng/api';
import { InventoryService, ILocationQuantityResult, IStockMovementResult } from '../../services/inventory.service';
import { InventoryApiService } from '../../services/inventory-api.service';
import { ItemLotService } from '../../services/item-lot.service';
import { LocationService } from '../../features/locations/services/location.service';
import { IInventoryItem, IInventoryLocationQuantity, InventoryStatus } from '../../models/inventory-item.model';
import { IStockMovement, MovementType, IStockMovementCreate } from '../../models/stock-movement.model';
import { ILocation } from '../../features/locations/models/location.model';
import { RevisionHistoryComponent } from '../revision-history/revision-history.component';
import { BillOfMaterialsComponent } from '../bill-of-materials/bill-of-materials.component';
import { WhereUsedComponent } from '../where-used/where-used.component';
import { LotListTableComponent } from '../lot-list-table/lot-list-table.component';

interface ILocationOption {
  label: string;
  value: string;
}

@Component({
  selector: 'app-inventory-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    CardModule,
    ButtonModule,
    TagModule,
    TableModule,
    TimelineModule,
    ToastModule,
    ConfirmDialogModule,
    DialogModule,
    InputNumberModule,
    InputTextModule,
    DropdownModule,
    BreadcrumbModule,
    TooltipModule,
    SkeletonModule,
    TabViewModule,
    RevisionHistoryComponent,
    BillOfMaterialsComponent,
    WhereUsedComponent,
    LotListTableComponent
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './inventory-detail.component.html',
  styleUrl: './inventory-detail.component.scss'
})
export class InventoryDetailComponent implements OnInit, OnDestroy {
  item: IInventoryItem | null = null;
  locationQuantities: IInventoryLocationQuantity[] = [];
  recentMovements: IStockMovement[] = [];
  totalMovements: number = 0;
  loading: boolean = true;
  loadingMovements: boolean = true;

  // Breadcrumb
  breadcrumbItems: MenuItem[] = [];
  breadcrumbHome: MenuItem = { icon: 'pi pi-home', routerLink: '/dashboard' };

  // Quick Adjust Dialog
  displayQuickAdjustDialog: boolean = false;
  quickAdjustQuantity: number = 0;
  quickAdjustReason: string = '';

  // Transfer Dialog
  displayTransferDialog: boolean = false;
  transferQuantity: number = 1;
  transferFromLocationId: string = '';
  transferToLocationId: string = '';
  transferLotId: string = '';
  transferNotes: string = '';
  locationOptions: ILocationOption[] = [];
  transferLotOptions: any[] = [];
  loadingTransferLots: boolean = false;

  // Event listener for BOM operations
  private bomOperationHandler = this.onBomOperation.bind(this);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private inventoryService: InventoryService,
    private itemLotService: ItemLotService,
    private locationService: LocationService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private inventoryApi: InventoryApiService
  ) { }

  ngOnInit() {
    const itemId = this.route.snapshot.paramMap.get('id');
    if (itemId) {
      this.loadItem(itemId);
      this.loadMovements(itemId);
      this.loadLocations();
    }

    // Listen for BOM build/unbuild operations to refresh item data
    window.addEventListener('bom-operation-complete', this.bomOperationHandler);
  }

  ngOnDestroy() {
    window.removeEventListener('bom-operation-complete', this.bomOperationHandler);
  }

  onBomOperation(event: Event) {
    // Refresh item data after BOM build/unbuild
    if (this.item?.id) {
      this.loadItem(this.item.id);
      this.loadMovements(this.item.id);
    }
  }

  loadItem(id: string) {
    this.loading = true;
    this.inventoryService.getItem(id).subscribe({
      next: (item: IInventoryItem) => {
        this.item = item;
        this.updateBreadcrumb();
        this.loadLocationQuantities(id);
        this.loading = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load item'
        });
        this.loading = false;
        this.router.navigate(['/inventory']);
      }
    });
  }

  loadLocationQuantities(id: string) {
    this.inventoryService.getItemLocationQuantities(id).subscribe({
      next: (result: ILocationQuantityResult) => {
        this.locationQuantities = result.items;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load location quantities'
        });
      }
    });
  }

  loadMovements(id: string) {
    this.loadingMovements = true;
    this.inventoryService.getItemMovements(id, 1, 10).subscribe({
      next: (result: IStockMovementResult) => {
        this.recentMovements = result.items;
        this.totalMovements = result.pagination.totalItems;
        this.loadingMovements = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load stock movements'
        });
        this.loadingMovements = false;
      }
    });
  }

  loadLocations() {
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

  updateBreadcrumb() {
    this.breadcrumbItems = [
      { label: 'Inventory', routerLink: '/inventory' },
      { label: this.item?.name || 'Item Details' }
    ];
  }

  // Status helpers
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

  getStatusSeverity(status: InventoryStatus): 'success' | 'warning' | 'danger' | 'info' | 'secondary' {
    const severities: Record<InventoryStatus, 'success' | 'warning' | 'danger' | 'info' | 'secondary'> = {
      [InventoryStatus.IN_STOCK]: 'success',
      [InventoryStatus.LOW_STOCK]: 'warning',
      [InventoryStatus.OUT_OF_STOCK]: 'danger',
      [InventoryStatus.ON_ORDER]: 'info',
      [InventoryStatus.DISCONTINUED]: 'secondary'
    };
    return severities[status] || 'secondary';
  }

  // Movement helpers
  getMovementIcon(type: MovementType): string {
    const icons: Record<MovementType, string> = {
      [MovementType.RECEIVE]: 'pi pi-arrow-down',
      [MovementType.SHIP]: 'pi pi-arrow-up',
      [MovementType.TRANSFER]: 'pi pi-arrows-h',
      [MovementType.ADJUST]: 'pi pi-sliders-h',
      [MovementType.COUNT]: 'pi pi-calculator'
    };
    return icons[type] || 'pi pi-circle';
  }

  getMovementColor(type: MovementType): string {
    const colors: Record<MovementType, string> = {
      [MovementType.RECEIVE]: '#10B981',
      [MovementType.SHIP]: '#F87171',
      [MovementType.TRANSFER]: '#6366F1',
      [MovementType.ADJUST]: '#F59E0B',
      [MovementType.COUNT]: '#64748B'
    };
    return colors[type] || '#64748B';
  }

  getMovementLabel(type: MovementType): string {
    const labels: Record<MovementType, string> = {
      [MovementType.RECEIVE]: 'Received',
      [MovementType.SHIP]: 'Shipped',
      [MovementType.TRANSFER]: 'Transferred',
      [MovementType.ADJUST]: 'Adjusted',
      [MovementType.COUNT]: 'Count'
    };
    return labels[type] || type;
  }

  formatDate(dateString: string | undefined): string {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // Actions
  editItem() {
    // Navigate to inventory list with edit mode (or could implement inline edit)
    this.router.navigate(['/inventory'], { queryParams: { edit: this.item?.id } });
  }

  deleteItem() {
    if (!this.item?.id) return;

    this.confirmationService.confirm({
      message: `Are you sure you want to delete "${this.item.name}"? This action cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.inventoryService.deleteItem(this.item!.id!).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Item deleted successfully'
            });
            this.router.navigate(['/inventory']);
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
    });
  }

  async generateBarcode(kind: 'code128' | 'ean13' | 'qr' = 'code128') {
    if (!this.item?.id) return;
    try {
      const updated = await this.inventoryApi.generateBarcode(this.item.id, kind);
      // Reload item to get fresh barcode image URL
      this.loadItem(this.item.id);
      // Navigate to barcode view route
      this.router.navigate(['/inventory', this.item.id, 'barcode']);
    } catch (e: any) {
      this.messageService.add({ severity: 'error', summary: 'Barcode', detail: 'Failed to generate barcode' });
    }
  }

  // Quick Adjust
  openQuickAdjust() {
    if (!this.item) return;
    this.quickAdjustQuantity = this.item.quantity;
    this.quickAdjustReason = '';
    this.displayQuickAdjustDialog = true;
  }

  saveQuickAdjust() {
    if (!this.item?.id) return;

    this.inventoryService.quickAdjust(
      this.item.id,
      this.quickAdjustQuantity,
      this.quickAdjustReason || undefined
    ).subscribe({
      next: (updatedItem: IInventoryItem) => {
        this.item = updatedItem;
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Quantity adjusted successfully'
        });
        this.displayQuickAdjustDialog = false;
        if (this.item?.id) {
          this.loadMovements(this.item.id);
        }
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

  // Transfer
  openTransfer() {
    this.transferQuantity = 1;
    this.transferFromLocationId = '';
    this.transferToLocationId = '';
    this.transferLotId = '';
    this.transferNotes = '';
    this.transferLotOptions = [];
    this.displayTransferDialog = true;
  }

  onTransferFromLocationChange() {
    this.transferLotId = '';
    this.transferLotOptions = [];
    this.loadTransferLots();
  }

  private loadTransferLots() {
    if (!this.item?.id || !this.transferFromLocationId) {
      this.transferLotOptions = [];
      return;
    }

    this.loadingTransferLots = true;
    const filters = {
      locationId: this.transferFromLocationId,
      includeExpired: false
    };

    this.itemLotService.getLotsForItem(this.item.id, 1, 1000, filters).subscribe({
      next: (response) => {
        this.transferLotOptions = (response.data || []).map(lot => ({
          label: `${lot.lotNumber}${lot.serialNumber ? ` (SN: ${lot.serialNumber})` : ''} - Qty: ${lot.quantity}`,
          value: lot.id
        }));
        this.loadingTransferLots = false;
      },
      error: () => {
        this.transferLotOptions = [];
        this.loadingTransferLots = false;
      }
    });
  }

  saveTransfer() {
    if (!this.item?.id || !this.transferFromLocationId || !this.transferToLocationId) return;

    const movement: IStockMovementCreate = {
      inventoryItemId: this.item.id,
      movementType: MovementType.TRANSFER,
      quantity: this.transferQuantity,
      fromLocationId: this.transferFromLocationId,
      toLocationId: this.transferToLocationId,
      lotId: this.transferLotId || undefined,
      notes: this.transferNotes || undefined
    };

    this.inventoryService.createStockMovement(movement).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Transfer completed successfully'
        });
        this.displayTransferDialog = false;
        this.loadItem(this.item!.id!);
        this.loadMovements(this.item!.id!);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to complete transfer'
        });
      }
    });
  }

  getAvailableFromLocations(): ILocationOption[] {
    // Only show locations where this item has quantity
    const locationsWithStock = this.locationQuantities
      .filter(lq => lq.quantity > 0)
      .map(lq => lq.locationId);
    return this.locationOptions.filter(opt => locationsWithStock.includes(opt.value));
  }

  getMaxTransferQuantity(): number {
    const fromLoc = this.locationQuantities.find(lq => lq.locationId === this.transferFromLocationId);
    return fromLoc?.quantity || 0;
  }
}
