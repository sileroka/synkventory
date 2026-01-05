import { Component, Input, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG Modules
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { DropdownModule } from 'primeng/dropdown';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { ProgressBarModule } from 'primeng/progressbar';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { MessageService, ConfirmationService } from 'primeng/api';
import { AutoCompleteModule, AutoCompleteCompleteEvent } from 'primeng/autocomplete';

import { BomService } from '../../services/bom.service';
import { InventoryService } from '../../services/inventory.service';
import {
  IBillOfMaterial,
  IBillOfMaterialCreate,
  IBOMAvailability,
  IBOMComponentAvailability,
} from '../../models/bill-of-material.model';
import { IInventoryItem } from '../../models/inventory-item.model';

@Component({
  selector: 'app-bill-of-materials',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputNumberModule,
    InputTextModule,
    InputTextareaModule,
    DropdownModule,
    TooltipModule,
    TagModule,
    ProgressBarModule,
    ConfirmDialogModule,
    ToastModule,
    AutoCompleteModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './bill-of-materials.component.html',
  styleUrls: ['./bill-of-materials.component.scss'],
})
export class BillOfMaterialsComponent implements OnInit {
  @Input() itemId!: string;
  @Input() itemName!: string;
  @Input() itemQuantity: number = 0;

  // State signals
  bomComponents = signal<IBillOfMaterial[]>([]);
  availability = signal<IBOMAvailability | null>(null);
  isLoading = signal(false);
  
  // Dialog state
  showAddDialog = signal(false);
  showBuildDialog = signal(false);
  showUnbuildDialog = signal(false);
  
  // Form data
  newComponent = signal<Partial<IBillOfMaterialCreate>>({
    quantityRequired: 1,
    unitOfMeasure: 'units',
    displayOrder: 0,
  });
  buildQuantity = signal(1);
  unbuildQuantity = signal(1);
  buildNotes = signal('');
  unbuildNotes = signal('');
  
  // Item search
  itemSuggestions = signal<IInventoryItem[]>([]);
  selectedItem = signal<IInventoryItem | null>(null);

  // Computed values
  hasBom = computed(() => this.bomComponents().length > 0);
  maxBuildable = computed(() => this.availability()?.maxBuildable ?? 0);
  canBuild = computed(() => this.maxBuildable() > 0 && this.buildQuantity() <= this.maxBuildable());
  canUnbuild = computed(() => this.itemQuantity > 0 && this.unbuildQuantity() <= this.itemQuantity);

  // Total cost of components
  totalComponentCost = computed(() => {
    return this.bomComponents().reduce((total, comp) => {
      const unitPrice = comp.componentItem?.unitPrice ?? 0;
      return total + (unitPrice * comp.quantityRequired);
    }, 0);
  });

  constructor(
    private bomService: BomService,
    private inventoryService: InventoryService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit(): void {
    this.loadBom();
  }

  loadBom(): void {
    if (!this.itemId) return;
    
    this.isLoading.set(true);
    
    this.bomService.getItemBom(this.itemId).subscribe({
      next: (components) => {
        this.bomComponents.set(components);
        if (components.length > 0) {
          this.loadAvailability();
        } else {
          this.availability.set(null);
        }
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error loading BOM:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load Bill of Materials',
        });
        this.isLoading.set(false);
      },
    });
  }

  loadAvailability(): void {
    this.bomService.getBuildAvailability(this.itemId).subscribe({
      next: (availability) => {
        this.availability.set(availability);
      },
      error: (error) => {
        console.error('Error loading availability:', error);
      },
    });
  }

  // Item search for autocomplete
  searchItems(event: AutoCompleteCompleteEvent): void {
    const query = event.query;
    
    this.inventoryService.getItems(1, 20, { search: query }).subscribe({
      next: (result) => {
        // Filter out the current item and items already in BOM
        const existingIds = new Set([
          this.itemId,
          ...this.bomComponents().map(c => c.componentItemId)
        ]);
        
        const filtered = result.items.filter(item => !existingIds.has(item.id!));
        this.itemSuggestions.set(filtered);
      },
      error: () => {
        this.itemSuggestions.set([]);
      },
    });
  }

  onItemSelect(item: IInventoryItem): void {
    this.selectedItem.set(item);
    this.newComponent.update(c => ({
      ...c,
      componentItemId: item.id!,
    }));
  }

  // Dialog handlers
  openAddDialog(): void {
    this.newComponent.set({
      quantityRequired: 1,
      unitOfMeasure: 'units',
      displayOrder: this.bomComponents().length,
    });
    this.selectedItem.set(null);
    this.showAddDialog.set(true);
  }

  closeAddDialog(): void {
    this.showAddDialog.set(false);
    this.selectedItem.set(null);
  }

  addComponent(): void {
    const component = this.newComponent();
    if (!component.componentItemId || !component.quantityRequired) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Please select a component and specify quantity',
      });
      return;
    }

    this.bomService.addBomComponent(this.itemId, component as IBillOfMaterialCreate).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Component added to BOM',
        });
        this.closeAddDialog();
        this.loadBom();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.error?.detail || 'Failed to add component',
        });
      },
    });
  }

  confirmDeleteComponent(component: IBillOfMaterial): void {
    this.confirmationService.confirm({
      message: `Remove "${component.componentItem?.name}" from the Bill of Materials?`,
      header: 'Confirm Removal',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.deleteComponent(component);
      },
    });
  }

  deleteComponent(component: IBillOfMaterial): void {
    this.bomService.deleteBomComponent(component.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Component removed from BOM',
        });
        this.loadBom();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.error?.detail || 'Failed to remove component',
        });
      },
    });
  }

  // Build dialog handlers
  openBuildDialog(): void {
    this.buildQuantity.set(1);
    this.buildNotes.set('');
    this.showBuildDialog.set(true);
  }

  closeBuildDialog(): void {
    this.showBuildDialog.set(false);
  }

  buildAssembly(): void {
    if (!this.canBuild()) return;

    this.bomService.buildAssembly(this.itemId, {
      quantityToBuild: this.buildQuantity(),
      notes: this.buildNotes() || undefined,
    }).subscribe({
      next: (result) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Build Complete',
          detail: result.message,
        });
        this.closeBuildDialog();
        this.loadBom();
        // Emit event to refresh parent item data
        window.dispatchEvent(new CustomEvent('bom-operation-complete', { detail: { type: 'build', result } }));
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Build Failed',
          detail: error.error?.detail || 'Failed to build assembly',
        });
      },
    });
  }

  // Unbuild dialog handlers
  openUnbuildDialog(): void {
    this.unbuildQuantity.set(1);
    this.unbuildNotes.set('');
    this.showUnbuildDialog.set(true);
  }

  closeUnbuildDialog(): void {
    this.showUnbuildDialog.set(false);
  }

  unbuildAssembly(): void {
    if (!this.canUnbuild()) return;

    this.bomService.unbuildAssembly(this.itemId, {
      quantityToUnbuild: this.unbuildQuantity(),
      notes: this.unbuildNotes() || undefined,
    }).subscribe({
      next: (result) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Disassembly Complete',
          detail: result.message,
        });
        this.closeUnbuildDialog();
        this.loadBom();
        // Emit event to refresh parent item data
        window.dispatchEvent(new CustomEvent('bom-operation-complete', { detail: { type: 'unbuild', result } }));
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Disassembly Failed',
          detail: error.error?.detail || 'Failed to disassemble',
        });
      },
    });
  }

  // Status helpers
  getStatusSeverity(status: string): 'success' | 'warning' | 'danger' | 'info' | 'secondary' {
    switch (status) {
      case 'in_stock': return 'success';
      case 'low_stock': return 'warning';
      case 'out_of_stock': return 'danger';
      default: return 'info';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'in_stock': return 'In Stock';
      case 'low_stock': return 'Low Stock';
      case 'out_of_stock': return 'Out of Stock';
      default: return status;
    }
  }

  getAvailabilityPercent(comp: IBOMComponentAvailability): number {
    if (comp.quantityRequired === 0) return 100;
    const ratio = comp.quantityAvailable / comp.quantityRequired;
    return Math.min(ratio * 100, 100);
  }

  getAvailabilityColor(comp: IBOMComponentAvailability): string {
    const percent = this.getAvailabilityPercent(comp);
    if (percent >= 100) return '#10B981'; // Success green
    if (percent >= 50) return '#F59E0B'; // Warning orange
    return '#EF4444'; // Danger red
  }
}
