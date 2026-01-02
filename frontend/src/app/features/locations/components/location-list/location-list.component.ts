import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule, TableLazyLoadEvent } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TagModule } from 'primeng/tag';
import { CheckboxModule } from 'primeng/checkbox';
import { MessageService, ConfirmationService } from 'primeng/api';
import { LocationService } from '../../services/location.service';
import { ILocation } from '../../models/location.model';

@Component({
  selector: 'app-location-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputTextareaModule,
    ToastModule,
    ConfirmDialogModule,
    TagModule,
    CheckboxModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './location-list.component.html',
  styleUrl: './location-list.component.scss'
})
export class LocationListComponent implements OnInit {
  locations: ILocation[] = [];
  displayDialog: boolean = false;
  selectedLocation: ILocation = this.getEmptyLocation();
  isEditMode: boolean = false;
  loading: boolean = false;

  // Pagination
  totalRecords: number = 0;
  currentPage: number = 1;
  pageSize: number = 25;

  constructor(
    private locationService: LocationService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.loadLocations();
  }

  loadLocations() {
    this.loading = true;
    this.locationService.getLocations(this.currentPage, this.pageSize).subscribe({
      next: (result) => {
        this.locations = result.items;
        this.totalRecords = result.pagination.totalItems;
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

  onPageChange(event: TableLazyLoadEvent) {
    this.currentPage = Math.floor((event.first || 0) / (event.rows || this.pageSize)) + 1;
    this.pageSize = event.rows || this.pageSize;
    this.loadLocations();
  }

  showAddDialog() {
    this.selectedLocation = this.getEmptyLocation();
    this.isEditMode = false;
    this.displayDialog = true;
  }

  showEditDialog(location: ILocation) {
    this.selectedLocation = { ...location };
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
          this.loadLocations();
          this.displayDialog = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to update location'
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
          this.loadLocations();
          this.displayDialog = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create location'
          });
        }
      });
    }
  }

  deleteLocation(location: ILocation) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete ${location.name}?`,
      accept: () => {
        if (location.id) {
          this.locationService.deleteLocation(location.id).subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Location deleted successfully'
              });
              this.loadLocations();
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

  getEmptyLocation(): ILocation {
    return {
      name: '',
      code: '',
      address: '',
      isActive: true
    };
  }
}
