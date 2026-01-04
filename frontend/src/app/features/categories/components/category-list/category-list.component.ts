import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TreeTableModule } from 'primeng/treetable';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TagModule } from 'primeng/tag';
import { CheckboxModule } from 'primeng/checkbox';
import { DropdownModule } from 'primeng/dropdown';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService, ConfirmationService, TreeNode } from 'primeng/api';
import { CategoryService } from '../../services/category.service';
import { ICategory, ICategoryTreeNode } from '../../models/category.model';
import { CategoryAttributesComponent } from '../category-attributes/category-attributes.component';

@Component({
  selector: 'app-category-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TreeTableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputTextareaModule,
    ToastModule,
    ConfirmDialogModule,
    TagModule,
    CheckboxModule,
    DropdownModule,
    TooltipModule,
    CategoryAttributesComponent
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './category-list.component.html',
  styleUrl: './category-list.component.scss'
})
export class CategoryListComponent implements OnInit {
  categories: TreeNode[] = [];
  flatCategories: ICategory[] = [];
  displayDialog: boolean = false;
  selectedCategory: ICategory = this.getEmptyCategory();
  isEditMode: boolean = false;
  loading: boolean = false;

  // Custom attributes panel state
  showAttributesPanel = signal(false);
  selectedCategoryForAttributes = signal<ICategory | null>(null);

  parentOptions: { label: string; value: string | null }[] = [];

  constructor(
    private categoryService: CategoryService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.loadCategories();
  }

  loadCategories() {
    this.loading = true;
    this.categoryService.getCategoryTree().subscribe({
      next: (tree) => {
        this.categories = this.transformToTreeNodes(tree);
        this.loadFlatCategories();
        this.loading = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load categories'
        });
        this.loading = false;
      }
    });
  }

  loadFlatCategories() {
    this.categoryService.getCategories(1, 1000).subscribe({
      next: (result) => {
        this.flatCategories = result.items;
        this.updateParentOptions();
      }
    });
  }

  updateParentOptions(excludeId?: string) {
    this.parentOptions = [
      { label: '(No Parent - Root Level)', value: null },
      ...this.flatCategories
        .filter(c => c.id !== excludeId)
        .map(c => ({ label: `${c.name} (${c.code})`, value: c.id! }))
    ];
  }

  transformToTreeNodes(categories: ICategoryTreeNode[]): TreeNode[] {
    return categories.map(category => ({
      data: category,
      children: category.children ? this.transformToTreeNodes(category.children) : [],
      expanded: true
    }));
  }

  showAddDialog(parentCategory?: ICategory) {
    this.selectedCategory = this.getEmptyCategory();
    if (parentCategory) {
      this.selectedCategory.parentId = parentCategory.id;
    }
    this.isEditMode = false;
    this.updateParentOptions();
    this.displayDialog = true;
  }

  showEditDialog(category: ICategory) {
    this.selectedCategory = { ...category };
    this.isEditMode = true;
    this.updateParentOptions(category.id);
    this.displayDialog = true;
  }

  saveCategory() {
    if (this.isEditMode && this.selectedCategory.id) {
      this.categoryService.updateCategory(this.selectedCategory.id, this.selectedCategory).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Category updated successfully'
          });
          this.loadCategories();
          this.displayDialog = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to update category'
          });
        }
      });
    } else {
      this.categoryService.createCategory(this.selectedCategory).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Category created successfully'
          });
          this.loadCategories();
          this.displayDialog = false;
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create category'
          });
        }
      });
    }
  }

  deleteCategory(category: ICategory) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete "${category.name}"?`,
      accept: () => {
        if (category.id) {
          this.categoryService.deleteCategory(category.id).subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Category deleted successfully'
              });
              this.loadCategories();
            },
            error: (err) => {
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: err.error?.error?.message || 'Failed to delete category'
              });
            }
          });
        }
      }
    });
  }

  getEmptyCategory(): ICategory {
    return {
      name: '',
      code: '',
      description: '',
      parentId: null,
      isActive: true
    };
  }

  // Custom attributes management
  openAttributesPanel(category: ICategory) {
    this.selectedCategoryForAttributes.set(category);
    this.showAttributesPanel.set(true);
  }

  closeAttributesPanel() {
    this.showAttributesPanel.set(false);
    this.selectedCategoryForAttributes.set(null);
  }
}
