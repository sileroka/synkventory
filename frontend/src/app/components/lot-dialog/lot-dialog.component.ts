import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { MessageModule } from 'primeng/message';
import { MessageService } from 'primeng/api';
import { DynamicDialogRef, DynamicDialogConfig } from 'primeng/dynamicdialog';
import { ItemLotService } from '../../../services/item-lot.service';
import { LocationService } from '../../../features/locations/services/location.service';
import { IItemLot, IItemLotCreate, IItemLotUpdate } from '../../../models/item-lot.model';
import { ILocation } from '../../../features/locations/models/location.model';

@Component({
  selector: 'app-lot-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    DialogModule,
    ButtonModule,
    InputTextModule,
    InputNumberModule,
    CalendarModule,
    DropdownModule,
    MessageModule
  ],
  templateUrl: './lot-dialog.component.html',
  styleUrls: ['./lot-dialog.component.scss']
})
export class LotDialogComponent implements OnInit {
  form!: FormGroup;
  isEditMode = false;
  lot: IItemLot | null = null;
  itemId: string = '';
  locations: ILocation[] = [];
  loading = false;
  submitting = false;
  lotNumberError = '';

  constructor(
    private fb: FormBuilder,
    private lotService: ItemLotService,
    private locationService: LocationService,
    private messageService: MessageService,
    public ref: DynamicDialogRef,
    public config: DynamicDialogConfig
  ) { }

  ngOnInit(): void {
    this.initializeForm();
    this.loadLocations();

    // Load existing lot if in edit mode
    if (this.config.data?.lot) {
      this.lot = this.config.data.lot;
      this.isEditMode = true;
      this.populateForm();
    }

    if (this.config.data?.itemId) {
      this.itemId = this.config.data.itemId;
    }
  }

  private initializeForm(): void {
    this.form = this.fb.group({
      lotNumber: ['', [Validators.required, Validators.minLength(3)]],
      serialNumber: [''],
      quantity: [1, [Validators.required, Validators.min(1)]],
      expirationDate: [null],
      manufactureDate: [null],
      locationId: [null]
    });
  }

  private populateForm(): void {
    if (!this.lot) return;

    this.form.patchValue({
      lotNumber: this.lot.lotNumber,
      serialNumber: this.lot.serialNumber || '',
      quantity: this.lot.quantity,
      expirationDate: this.lot.expirationDate ? new Date(this.lot.expirationDate) : null,
      manufactureDate: this.lot.manufactureDate ? new Date(this.lot.manufactureDate) : null,
      locationId: this.lot.locationId || null
    });
  }

  private loadLocations(): void {
    this.loading = true;
    this.locationService.getLocations(1, 1000).subscribe({
      next: (response) => {
        this.locations = response.data || [];
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  onSubmit(): void {
    if (!this.form.valid) {
      return;
    }

    this.submitting = true;
    const formValue = this.form.value;

    // Convert dates to ISO date strings
    const payload: IItemLotCreate | IItemLotUpdate = {
      lotNumber: formValue.lotNumber,
      serialNumber: formValue.serialNumber || null,
      quantity: formValue.quantity,
      expirationDate: formValue.expirationDate
        ? this.formatDateToISO(formValue.expirationDate)
        : null,
      manufactureDate: formValue.manufactureDate
        ? this.formatDateToISO(formValue.manufactureDate)
        : null,
      locationId: formValue.locationId || null
    };

    if (this.isEditMode && this.lot) {
      this.lotService.updateLot(this.lot.id, payload as IItemLotUpdate).subscribe({
        next: (response) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Lot updated successfully',
            life: 3000
          });
          this.submitting = false;
          this.ref.close(response.data);
        },
        error: (error) => {
          this.handleError(error);
          this.submitting = false;
        }
      });
    } else {
      this.lotService.createLot(this.itemId, payload as IItemLotCreate).subscribe({
        next: (response) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Lot created successfully',
            life: 3000
          });
          this.submitting = false;
          this.ref.close(response.data);
        },
        error: (error) => {
          this.handleError(error);
          this.submitting = false;
        }
      });
    }
  }

  onCancel(): void {
    this.ref.close();
  }

  private formatDateToISO(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  private handleError(error: any): void {
    const errorMessage = error?.error?.error?.message || 'An error occurred';
    this.messageService.add({
      severity: 'error',
      summary: 'Error',
      detail: errorMessage,
      life: 5000
    });

    if (errorMessage.includes('duplicate') || errorMessage.includes('already exists')) {
      this.lotNumberError = 'This lot number already exists for your tenant';
    }
  }

  get locationOptions(): any[] {
    return this.locations.map(loc => ({
      label: `${loc.name}${loc.code ? ` (${loc.code})` : ''}`,
      value: loc.id
    }));
  }

  isExpirationDatePassed(): boolean {
    const expirationDate = this.form.get('expirationDate')?.value;
    if (!expirationDate) return false;
    return new Date(expirationDate) < new Date();
  }
}
