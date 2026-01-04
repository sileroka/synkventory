import { Component, inject, OnInit, signal, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { DropdownModule } from 'primeng/dropdown';
import { CheckboxModule } from 'primeng/checkbox';
import { InputNumberModule } from 'primeng/inputnumber';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { MessageService, ConfirmationService } from 'primeng/api';
import { CategoryAttributeService } from '../../../../services/category-attribute.service';
import {
  ICategoryAttribute,
  ICategoryAttributeCreate,
  AttributeType,
  AttributeTypeLabels,
  AttributeTypeIcons,
} from '../../../../models/category-attribute.model';

interface AttributeTypeOption {
  label: string;
  value: AttributeType;
  icon: string;
}

@Component({
  selector: 'app-category-attributes',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputTextareaModule,
    DropdownModule,
    CheckboxModule,
    InputNumberModule,
    ToastModule,
    ConfirmDialogModule,
    TooltipModule,
    TagModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './category-attributes.component.html',
  styleUrl: './category-attributes.component.scss',
})
export class CategoryAttributesComponent implements OnInit {
  private attributeService = inject(CategoryAttributeService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  // Inputs
  categoryId = input.required<string>();
  categoryName = input<string>('');

  // Outputs
  closed = output<void>();

  // State
  attributes = signal<ICategoryAttribute[]>([]);
  isLoading = signal(true);
  showDialog = signal(false);
  isEditMode = signal(false);
  isSaving = signal(false);

  // Form data
  selectedAttribute: Partial<ICategoryAttributeCreate> = this.getEmptyAttribute();

  // Options
  attributeTypes: AttributeTypeOption[] = [
    { label: 'Text', value: 'text', icon: 'pi pi-pencil' },
    { label: 'Number', value: 'number', icon: 'pi pi-hashtag' },
    { label: 'Yes/No', value: 'boolean', icon: 'pi pi-check-square' },
    { label: 'Date', value: 'date', icon: 'pi pi-calendar' },
    { label: 'Dropdown', value: 'select', icon: 'pi pi-list' },
  ];

  // Labels for display
  typeLabels = AttributeTypeLabels;
  typeIcons = AttributeTypeIcons;

  ngOnInit(): void {
    this.loadAttributes();
  }

  loadAttributes(): void {
    this.isLoading.set(true);
    this.attributeService.getAttributesByCategory(this.categoryId(), true).subscribe({
      next: (result) => {
        this.attributes.set(result.items);
        this.isLoading.set(false);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load attributes',
        });
        this.isLoading.set(false);
      },
    });
  }

  getEmptyAttribute(): Partial<ICategoryAttributeCreate> {
    return {
      name: '',
      key: '',
      attributeType: 'text',
      description: '',
      options: '',
      isRequired: false,
      defaultValue: '',
      displayOrder: 0,
    };
  }

  showAddDialog(): void {
    this.selectedAttribute = this.getEmptyAttribute();
    this.isEditMode.set(false);
    this.showDialog.set(true);
  }

  showEditDialog(attr: ICategoryAttribute): void {
    this.selectedAttribute = { ...attr };
    this.isEditMode.set(true);
    this.showDialog.set(true);
  }

  saveAttribute(): void {
    if (!this.selectedAttribute.name) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Attribute name is required',
      });
      return;
    }

    // Auto-generate key from name if not set
    if (!this.selectedAttribute.key) {
      this.selectedAttribute.key = this.selectedAttribute.name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_|_$/g, '');
    }

    this.isSaving.set(true);

    if (this.isEditMode()) {
      const id = (this.selectedAttribute as ICategoryAttribute).id;
      this.attributeService
        .updateAttribute(id, {
          name: this.selectedAttribute.name,
          description: this.selectedAttribute.description,
          options: this.selectedAttribute.options,
          isRequired: this.selectedAttribute.isRequired,
          defaultValue: this.selectedAttribute.defaultValue,
          displayOrder: this.selectedAttribute.displayOrder,
        })
        .subscribe({
          next: (updated) => {
            this.attributes.update((list) =>
              list.map((a) => (a.id === updated.id ? updated : a))
            );
            this.showDialog.set(false);
            this.isSaving.set(false);
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Attribute updated',
            });
          },
          error: (err) => {
            this.isSaving.set(false);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: err.error?.detail || 'Failed to update attribute',
            });
          },
        });
    } else {
      this.attributeService
        .createAttribute(this.categoryId(), this.selectedAttribute as ICategoryAttributeCreate)
        .subscribe({
          next: (created) => {
            this.attributes.update((list) => [...list, created]);
            this.showDialog.set(false);
            this.isSaving.set(false);
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Attribute created',
            });
          },
          error: (err) => {
            this.isSaving.set(false);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: err.error?.detail || 'Failed to create attribute',
            });
          },
        });
    }
  }

  confirmDelete(attr: ICategoryAttribute): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete "${attr.name}"? This won't remove values from existing items.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.deleteAttribute(attr);
      },
    });
  }

  deleteAttribute(attr: ICategoryAttribute): void {
    this.attributeService.deleteAttribute(attr.id).subscribe({
      next: () => {
        this.attributes.update((list) => list.filter((a) => a.id !== attr.id));
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Attribute deleted',
        });
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete attribute',
        });
      },
    });
  }

  toggleActive(attr: ICategoryAttribute): void {
    this.attributeService
      .updateAttribute(attr.id, { isActive: !attr.isActive })
      .subscribe({
        next: (updated) => {
          this.attributes.update((list) =>
            list.map((a) => (a.id === updated.id ? updated : a))
          );
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to update attribute',
          });
        },
      });
  }

  getTypeLabel(type: AttributeType): string {
    return this.typeLabels[type] || type;
  }

  getTypeIcon(type: AttributeType): string {
    return this.typeIcons[type] || 'pi pi-question';
  }

  close(): void {
    this.closed.emit();
  }
}
