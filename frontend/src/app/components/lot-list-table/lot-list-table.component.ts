import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MessageService, ConfirmationService, MenuItem } from 'primeng/api';
import { DialogService, DynamicDialogRef } from 'primeng/dynamicdialog';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MenuModule } from 'primeng/menu';
import { TooltipModule } from 'primeng/tooltip';
import { InputSwitchModule } from 'primeng/inputswitch';
import { FormsModule } from '@angular/forms';
import { Table } from 'primeng/table';
import { ItemLotService } from '../../../services/item-lot.service';
import { LotDialogComponent } from '../lot-dialog/lot-dialog.component';
import { IItemLot, ILotFilters } from '../../../models/item-lot.model';
import { ILocation } from '../../../features/locations/models/location.model';
import { LocationService } from '../../../features/locations/services/location.service';

@Component({
  selector: 'app-lot-list-table',
  standalone: true,
  imports: [
    CommonModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    TagModule,
    ToastModule,
    ConfirmDialogModule,
    MenuModule,
    TooltipModule,
    InputSwitchModule,
    FormsModule
  ],
  templateUrl: './lot-list-table.component.html',
  styleUrls: ['./lot-list-table.component.scss'],
  providers: [DialogService, MessageService, ConfirmationService]
})
export class LotListTableComponent implements OnInit {
  @Input() itemId: string = '';
  @ViewChild('dt') table!: Table;

  lots: IItemLot[] = [];
  locations: ILocation[] = [];
  loading = false;
  totalRecords = 0;
  pageSize = 25;
  currentPage = 1;

  // Filters
  selectedLocationId: string | null = null;
  includeExpired = false;
  orderBy: 'created_at' | 'expiration_date' | 'lot_number' = 'created_at';

  dialogRef!: DynamicDialogRef;

  constructor(
    private lotService: ItemLotService,
    private locationService: LocationService,
    private dialogService: DialogService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) { }

  ngOnInit(): void {
    this.loadLocations();
    this.loadLots();
  }

  private loadLocations(): void {
    this.locationService.getLocations(1, 1000).subscribe({
      next: (response) => {
        this.locations = response.data || [];
      }
    });
  }

  loadLots(): void {
    if (!this.itemId) return;

    this.loading = true;
    const filters: ILotFilters = {
      locationId: this.selectedLocationId || undefined,
      includeExpired: this.includeExpired,
      orderBy: this.orderBy
    };

    this.lotService.getLotsForItem(this.itemId, this.currentPage, this.pageSize, filters).subscribe({
      next: (response) => {
        this.lots = response.data || [];
        this.totalRecords = response.meta?.totalItems || 0;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load lots',
          life: 3000
        });
      }
    });
  }

  onPageChange(event: any): void {
    this.currentPage = event.first / event.rows + 1;
    this.pageSize = event.rows;
    this.loadLots();
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadLots();
  }

  openCreateDialog(): void {
    this.dialogRef = this.dialogService.open(LotDialogComponent, {
      width: '100%',
      maxWidth: '600px',
      data: { itemId: this.itemId }
    });

    this.dialogRef.onClose.subscribe((result: IItemLot | undefined) => {
      if (result) {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Lot created successfully',
          life: 3000
        });
        this.loadLots();
      }
    });
  }

  openEditDialog(lot: IItemLot): void {
    this.dialogRef = this.dialogService.open(LotDialogComponent, {
      width: '100%',
      maxWidth: '600px',
      data: { lot, itemId: this.itemId }
    });

    this.dialogRef.onClose.subscribe((result: IItemLot | undefined) => {
      if (result) {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Lot updated successfully',
          life: 3000
        });
        this.loadLots();
      }
    });
  }

  confirmDelete(lot: IItemLot): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete lot "${lot.lotNumber}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.deleteLot(lot);
      }
    });
  }

  private deleteLot(lot: IItemLot): void {
    this.lotService.deleteLot(lot.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Lot "${lot.lotNumber}" deleted successfully`,
          life: 3000
        });
        this.loadLots();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete lot',
          life: 3000
        });
      }
    });
  }

  getExpirationStatus(lot: IItemLot): { severity: string; label: string } {
    if (!lot.expirationDate) {
      return { severity: 'info', label: 'No expiration' };
    }

    const expirationDate = new Date(lot.expirationDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    expirationDate.setHours(0, 0, 0, 0);

    if (expirationDate < today) {
      return { severity: 'danger', label: 'Expired' };
    }

    const daysUntilExpiration = Math.floor(
      (expirationDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysUntilExpiration <= 30) {
      return { severity: 'warning', label: `Expires in ${daysUntilExpiration} days` };
    }

    return { severity: 'success', label: 'Active' };
  }

  getLocationName(locationId: string | null): string {
    if (!locationId) return 'Unassigned';
    const location = this.locations.find(l => l.id === locationId);
    return location ? `${location.name}${location.code ? ` (${location.code})` : ''}` : 'Unknown';
  }

  get locationOptions(): any[] {
    return [
      { label: 'All Locations', value: null },
      ...this.locations.map(loc => ({
        label: `${loc.name}${loc.code ? ` (${loc.code})` : ''}`,
        value: loc.id
      }))
    ];
  }

  get orderByOptions(): any[] {
    return [
      { label: 'Created Date', value: 'created_at' },
      { label: 'Expiration Date', value: 'expiration_date' },
      { label: 'Lot Number', value: 'lot_number' }
    ];
  }
}
