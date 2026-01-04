import { Component, OnInit, signal, inject } from '@angular/core';
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
import { TabViewModule } from 'primeng/tabview';
import { CardModule } from 'primeng/card';
import { MessageService, ConfirmationService } from 'primeng/api';
import { CategoryService } from '../../categories/services/category.service';
import { CategoryAttributeService } from '../../../services/category-attribute.service';
import { ICategory } from '../../categories/models/category.model';
import {
  ICategoryAttribute,
  ICategoryAttributeCreate,
  AttributeType,
  AttributeTypeLabels,
  AttributeTypeIcons,
} from '../../../models/category-attribute.model';

interface AttributeTypeOption {
  label: string;
  value: AttributeType;
  icon: string;
}

// Attribute type values as array for iteration
const ATTRIBUTE_TYPES: AttributeType[] = ['text', 'number', 'boolean', 'date', 'select'];

@Component({
  selector: 'app-custom-fields',
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
    TabViewModule,
    CardModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './custom-fields.component.html',
  styleUrl: './custom-fields.component.scss',
})
export class CustomFieldsComponent implements OnInit {
  private categoryService = inject(CategoryService);
  private attributeService = inject(CategoryAttributeService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  // State
  categories = signal<ICategory[]>([]);
  selectedCategory = signal<ICategory | null>(null);
  attributes = signal<ICategoryAttribute[]>([]);
  loading = signal(false);
  attributesLoading = signal(false);

  // Dialog state
  displayDialog = signal(false);
  isEditMode = signal(false);
  currentAttribute: ICategoryAttributeCreate = this.getEmptyAttribute();
  editingAttributeId: string | null = null;

  // Attribute type options
  attributeTypeOptions: AttributeTypeOption[] = ATTRIBUTE_TYPES.map(
    (type) => ({
      label: AttributeTypeLabels[type],
      value: type,
      icon: AttributeTypeIcons[type],
    })
  );

  ngOnInit() {
    this.loadCategories();
  }

  loadCategories() {
    this.loading.set(true);
    this.categoryService.getCategories(1, 1000).subscribe({
      next: (result) => {
        this.categories.set(result.items);
        this.loading.set(false);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load categories',
        });
        this.loading.set(false);
      },
    });
  }

  selectCategory(category: ICategory) {
    this.selectedCategory.set(category);
    if (category.id) {
      this.loadAttributes(category.id);
    }
  }

  loadAttributes(categoryId: string) {
    this.attributesLoading.set(true);
    this.attributeService.getAttributesByCategory(categoryId).subscribe({
      next: (response) => {
        this.attributes.set(response.items);
        this.attributesLoading.set(false);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load attributes',
        });
        this.attributesLoading.set(false);
      },
    });
  }

  showAddDialog() {
    if (!this.selectedCategory()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Select Category',
        detail: 'Please select a category first',
      });
      return;
    }
    this.currentAttribute = this.getEmptyAttribute();
    this.isEditMode.set(false);
    this.editingAttributeId = null;
    this.displayDialog.set(true);
  }

  showEditDialog(attribute: ICategoryAttribute) {
    this.currentAttribute = {
      categoryId: attribute.categoryId,
      name: attribute.name,
      key: attribute.key,
      description: attribute.description || '',
      attributeType: attribute.attributeType,
      isRequired: attribute.isRequired,
      defaultValue: attribute.defaultValue,
      options: attribute.options,
      displayOrder: attribute.displayOrder,
    };
    this.isEditMode.set(true);
    this.editingAttributeId = attribute.id;
    this.displayDialog.set(true);
  }

  saveAttribute() {
    const category = this.selectedCategory();
    if (!category || !category.id) return;

    // Set categoryId
    this.currentAttribute.categoryId = category.id;

    // Generate key from name if not set
    if (!this.currentAttribute.key) {
      this.currentAttribute.key = this.currentAttribute.name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_|_$/g, '');
    }

    if (this.isEditMode() && this.editingAttributeId) {
      this.attributeService
        .updateAttribute(this.editingAttributeId, this.currentAttribute)
        .subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Attribute updated successfully',
            });
            this.displayDialog.set(false);
            if (category.id) this.loadAttributes(category.id);
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to update attribute',
            });
          },
        });
    } else {
      this.attributeService
        .createAttribute(category.id, this.currentAttribute)
        .subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Attribute created successfully',
            });
            this.displayDialog.set(false);
            if (category.id) this.loadAttributes(category.id);
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to create attribute',
            });
          },
        });
    }
  }

  deleteAttribute(attribute: ICategoryAttribute) {
    const category = this.selectedCategory();
    if (!category || !category.id) return;

    this.confirmationService.confirm({
      message: `Are you sure you want to delete the attribute "${attribute.name}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.attributeService.deleteAttribute(attribute.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Attribute deleted successfully',
            });
            if (category.id) this.loadAttributes(category.id);
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete attribute',
            });
          },
        });
      },
    });
  }

  getTypeLabel(type: AttributeType): string {
    return AttributeTypeLabels[type] || type;
  }

  getTypeIcon(type: AttributeType): string {
    return AttributeTypeIcons[type] || 'pi-question';
  }

  getTypeSeverity(type: AttributeType): 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast' {
    const severityMap: Record<AttributeType, 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast'> = {
      'text': 'info',
      'number': 'success',
      'boolean': 'warning',
      'date': 'secondary',
      'select': 'contrast',
    };
    return severityMap[type] || 'info';
  }

  private getEmptyAttribute(): ICategoryAttributeCreate {
    return {
      categoryId: '',
      name: '',
      key: '',
      description: '',
      attributeType: 'text',
      isRequired: false,
      defaultValue: undefined,
      options: undefined,
      displayOrder: 0,
    };
  }
}
