import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TreeTableModule } from 'primeng/treetable';
import { TreeNode } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { InputNumberModule } from 'primeng/inputnumber';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TagModule } from 'primeng/tag';
import { CheckboxModule } from 'primeng/checkbox';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService, ConfirmationService } from 'primeng/api';
import { LocationService } from '../../services/location.service';
import {
  ILocation,
  ILocationTreeNode,
  LocationType,
  LOCATION_TYPE_DISPLAY_NAMES,
  LOCATION_TYPE_HIERARCHY,
  getLocationTypeIcon
} from '../../models/location.model';

interface LocationTypeOption {
  label: string;
  value: LocationType;
}

@Component({
  selector: 'app-location-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TreeTableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputTextareaModule,
    InputNumberModule,
    DropdownModule,
    ToastModule,
    ConfirmDialogModule,
    TagModule,
    CheckboxModule,
    TooltipModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './location-list.component.html',
  styleUrl: './location-list.component.scss'
})
export class LocationListComponent implements OnInit {
  locationTree: TreeNode[] = [];
  displayDialog: boolean = false;
  selectedLocation: ILocation = this.getEmptyLocation();
  parentLocation: ILocationTreeNode | null = null;
  isEditMode: boolean = false;
  loading: boolean = false;

  // Location type options for dropdown
  locationTypeOptions: LocationTypeOption[] = [
    { label: 'Warehouse', value: 'warehouse' },
    { label: 'Row', value: 'row' },
    { label: 'Bay', value: 'bay' },
    { label: 'Level', value: 'level' },
    { label: 'Position', value: 'position' }
  ];

  constructor(
    private locationService: LocationService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.loadLocationTree();
  }

  loadLocationTree() {
    this.loading = true;
    this.locationService.getLocationTree().subscribe({
      next: (tree) => {
        this.locationTree = this.convertToTreeNodes(tree);
        this.loading = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load locations'
        });
        this.loading = false;
      }
    });
  }

  convertToTreeNodes(locations: ILocationTreeNode[]): TreeNode[] {
    return locations.map(loc => ({
      data: loc,
      children: loc.children ? this.convertToTreeNodes(loc.children) : [],
      expanded: loc.locationType === 'warehouse' // Auto-expand warehouses
    }));
  }

  getLocationTypeIcon(type: LocationType): string {
    return getLocationTypeIcon(type);
  }

  getLocationTypeLabel(type: LocationType): string {
    return LOCATION_TYPE_DISPLAY_NAMES[type] || type;
  }

  getLocationTypeSeverity(type: LocationType): 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast' {
    const severities: Record<LocationType, 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast'> = {
      warehouse: 'info',
      row: 'success',
      bay: 'warning',
      level: 'secondary',
      position: 'contrast'
    };
    return severities[type] || 'info';
  }

  canAddChild(location: ILocationTreeNode): boolean {
    return LOCATION_TYPE_HIERARCHY[location.locationType] !== null;
  }

  getChildTypeLabel(location: ILocationTreeNode): string {
    const childType = LOCATION_TYPE_HIERARCHY[location.locationType];
    return childType ? LOCATION_TYPE_DISPLAY_NAMES[childType] : '';
  }

  showAddWarehouseDialog() {
    this.selectedLocation = this.getEmptyLocation('warehouse');
    this.parentLocation = null;
    this.isEditMode = false;
    this.displayDialog = true;
  }

  showAddChildDialog(parent: ILocationTreeNode) {
    const childType = LOCATION_TYPE_HIERARCHY[parent.locationType];
    if (!childType) return;

    this.selectedLocation = this.getEmptyLocation(childType);
    this.selectedLocation.parentId = parent.id;
    this.parentLocation = parent;
    this.isEditMode = false;
    this.displayDialog = true;
  }

  showEditDialog(location: ILocationTreeNode) {
    this.selectedLocation = {
      id: location.id,
      name: location.name,
      code: location.code,
      locationType: location.locationType,
      parentId: location.parentId,
      description: location.description,
      address: location.address,
      barcode: location.barcode,
      capacity: location.capacity,
      sortOrder: location.sortOrder,
      isActive: location.isActive
    };
    this.parentLocation = null;
    this.isEditMode = true;
    this.displayDialog = true;
  }

  saveLocation() {
    if (this.isEditMode && this.selectedLocation.id) {
      this.locationService.updateLocation(this.selectedLocation.id, this.selectedLocation).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Location updated successfully'
          });
          this.loadLocationTree();
          this.displayDialog = false;
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: err.error?.error?.message || 'Failed to update location'
          });
        }
      });
    } else {
      this.locationService.createLocation(this.selectedLocation).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Location created successfully'
          });
          this.loadLocationTree();
          this.displayDialog = false;
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: err.error?.error?.message || 'Failed to create location'
          });
        }
      });
    }
  }

  deleteLocation(location: ILocationTreeNode) {
    const hasChildren = location.children && location.children.length > 0;
    const message = hasChildren
      ? `Are you sure you want to delete "${location.name}" and all its ${location.children.length} child location(s)?`
      : `Are you sure you want to delete "${location.name}"?`;

    this.confirmationService.confirm({
      message,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        if (location.id) {
          this.locationService.deleteLocation(location.id).subscribe({
            next: (msg) => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: msg
              });
              this.loadLocationTree();
            },
            error: () => {
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to delete location'
              });
            }
          });
        }
      }
    });
  }

  getDialogTitle(): string {
    if (this.isEditMode) {
      return `Edit ${this.getLocationTypeLabel(this.selectedLocation.locationType)}`;
    }
    if (this.parentLocation) {
      return `Add ${this.getLocationTypeLabel(this.selectedLocation.locationType)} to ${this.parentLocation.name}`;
    }
    return 'Add Warehouse';
  }

  getEmptyLocation(type: LocationType = 'warehouse'): ILocation {
    return {
      name: '',
      code: '',
      locationType: type,
      parentId: null,
      description: '',
      address: '',
      barcode: '',
      capacity: undefined,
      sortOrder: 0,
      isActive: true
    };
  }
}
