import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { InventoryService } from '../../services/inventory.service';
import { IInventoryItem } from '../../models/inventory-item.model';

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
    ConfirmDialogModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './inventory-list.component.html',
  styleUrl: './inventory-list.component.scss'
})
export class InventoryListComponent implements OnInit {
  items: IInventoryItem[] = [];
  displayDialog: boolean = false;
  selectedItem: IInventoryItem = this.getEmptyItem();
  isEditMode: boolean = false;
  loading: boolean = false;

  constructor(
    private inventoryService: InventoryService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.loadItems();
  }

  loadItems() {
    this.loading = true;
    this.inventoryService.getItems().subscribe({
      next: (data) => {
        this.items = data;
        this.loading = false;
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load inventory items'
        });
        this.loading = false;
      }
    });
  }

  showAddDialog() {
    this.selectedItem = this.getEmptyItem();
    this.isEditMode = false;
    this.displayDialog = true;
  }

  showEditDialog(item: IInventoryItem) {
    this.selectedItem = { ...item };
    this.isEditMode = true;
    this.displayDialog = true;
  }

  saveItem() {
    if (this.isEditMode && this.selectedItem.id) {
      this.inventoryService.updateItem(this.selectedItem.id, this.selectedItem).subscribe({
        next: () => {
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
        next: () => {
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
      unit_price: 0,
      category: '',
      location: ''
    };
  }
}
