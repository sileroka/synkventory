import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ConfirmationService, MessageService } from 'primeng/api';
import { InventoryListComponent } from './inventory-list.component';
import { InventoryService, IInventoryListResult } from '../../services/inventory.service';
import { LocationService, ILocationListResult } from '../../features/locations/services/location.service';
import { CategoryService, ICategoryListResult } from '../../features/categories/services/category.service';
import { IInventoryItem, InventoryStatus } from '../../models/inventory-item.model';
import { IPaginationMeta } from '../../models/api-response.model';

describe('InventoryListComponent', () => {
  let component: InventoryListComponent;
  let fixture: ComponentFixture<InventoryListComponent>;
  let inventoryServiceSpy: jasmine.SpyObj<InventoryService>;
  let locationServiceSpy: jasmine.SpyObj<LocationService>;
  let categoryServiceSpy: jasmine.SpyObj<CategoryService>;
  let messageServiceSpy: jasmine.SpyObj<MessageService>;
  let confirmationServiceSpy: jasmine.SpyObj<ConfirmationService>;
  let routerSpy: jasmine.SpyObj<Router>;

  // Mock data matching IInventoryItem interface
  const mockPaginationMeta: IPaginationMeta = {
    page: 1,
    pageSize: 25,
    totalItems: 2,
    totalPages: 1,
    timestamp: '2026-01-01T00:00:00Z',
    requestId: 'test-request-id'
  };

  const mockInventoryItem: IInventoryItem = {
    id: '550e8400-e29b-41d4-a716-446655440001',
    name: 'Test Widget',
    sku: 'TEST-001',
    description: 'A test widget for unit testing',
    quantity: 100,
    reorderPoint: 10,
    unitPrice: 29.99,
    status: InventoryStatus.IN_STOCK,
    categoryId: '550e8400-e29b-41d4-a716-446655440010',
    locationId: '550e8400-e29b-41d4-a716-446655440020',
    category: { id: '550e8400-e29b-41d4-a716-446655440010', name: 'Electronics' },
    location: { id: '550e8400-e29b-41d4-a716-446655440020', name: 'Warehouse A', code: 'WH-A' },
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T12:00:00Z'
  };

  const mockInventoryItem2: IInventoryItem = {
    id: '550e8400-e29b-41d4-a716-446655440002',
    name: 'Test Gadget',
    sku: 'TEST-002',
    description: 'A test gadget for unit testing',
    quantity: 5,
    reorderPoint: 20,
    unitPrice: 49.99,
    status: InventoryStatus.LOW_STOCK,
    categoryId: null,
    locationId: null,
    category: null,
    location: null,
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T12:00:00Z'
  };

  const mockInventoryListResult: IInventoryListResult = {
    items: [mockInventoryItem, mockInventoryItem2],
    pagination: mockPaginationMeta
  };

  const mockEmptyListResult: IInventoryListResult = {
    items: [],
    pagination: { ...mockPaginationMeta, totalItems: 0, totalPages: 0 }
  };

  const mockLocationListResult: ILocationListResult = {
    items: [
      { id: '550e8400-e29b-41d4-a716-446655440020', name: 'Warehouse A', code: 'WH-A', isActive: true }
    ],
    pagination: mockPaginationMeta
  };

  const mockCategoryListResult: ICategoryListResult = {
    items: [
      { id: '550e8400-e29b-41d4-a716-446655440010', name: 'Electronics', isActive: true }
    ],
    pagination: mockPaginationMeta
  };

  beforeEach(async () => {
    inventoryServiceSpy = jasmine.createSpyObj('InventoryService', [
      'getItems',
      'getItem',
      'createItem',
      'updateItem',
      'deleteItem',
      'bulkDelete',
      'bulkStatusUpdate',
      'quickAdjust',
      'getItemLocationQuantities'
    ]);

    locationServiceSpy = jasmine.createSpyObj('LocationService', ['getLocations']);
    categoryServiceSpy = jasmine.createSpyObj('CategoryService', ['getCategories']);
    messageServiceSpy = jasmine.createSpyObj('MessageService', ['add']);
    confirmationServiceSpy = jasmine.createSpyObj('ConfirmationService', ['confirm']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    // Set up default return values
    inventoryServiceSpy.getItems.and.returnValue(of(mockInventoryListResult));
    locationServiceSpy.getLocations.and.returnValue(of(mockLocationListResult));
    categoryServiceSpy.getCategories.and.returnValue(of(mockCategoryListResult));

    await TestBed.configureTestingModule({
      imports: [
        InventoryListComponent,
        HttpClientTestingModule,
        NoopAnimationsModule
      ],
      providers: [
        { provide: InventoryService, useValue: inventoryServiceSpy },
        { provide: LocationService, useValue: locationServiceSpy },
        { provide: CategoryService, useValue: categoryServiceSpy },
        { provide: MessageService, useValue: messageServiceSpy },
        { provide: ConfirmationService, useValue: confirmationServiceSpy },
        { provide: Router, useValue: routerSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InventoryListComponent);
    component = fixture.componentInstance;
  });

  describe('Component Creation', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should have default values initialized', () => {
      expect(component.items).toEqual([]);
      expect(component.loading).toBeFalse();
      expect(component.displayDialog).toBeFalse();
      expect(component.isEditMode).toBeFalse();
      expect(component.currentPage).toBe(1);
      expect(component.pageSize).toBe(25);
    });

    it('should have status options defined', () => {
      expect(component.statusOptions.length).toBe(5);
      expect(component.statusOptions[0].value).toBe(InventoryStatus.IN_STOCK);
    });
  });

  describe('Loading Items on Init', () => {
    it('should load items on init', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(inventoryServiceSpy.getItems).toHaveBeenCalledWith(1, 25, jasmine.any(Object));
      expect(component.items.length).toBe(2);
      expect(component.items[0]).toEqual(mockInventoryItem);
      expect(component.totalRecords).toBe(2);
    }));

    it('should load locations on init', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(locationServiceSpy.getLocations).toHaveBeenCalledWith(1, 100, true);
      expect(component.locationOptions.length).toBe(2); // Including 'None' option
    }));

    it('should load categories on init', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(categoryServiceSpy.getCategories).toHaveBeenCalledWith(1, 100, true);
      expect(component.categoryOptions.length).toBe(2); // Including 'None' option
    }));

    it('should set loading to true while fetching items', () => {
      component.loadItems();
      expect(component.loading).toBeTrue();
    });

    it('should set loading to false after items are loaded', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.loading).toBeFalse();
    }));

    it('should show error message when loading items fails', fakeAsync(() => {
      inventoryServiceSpy.getItems.and.returnValue(throwError(() => new Error('Network error')));
      fixture.detectChanges();
      tick();

      expect(messageServiceSpy.add).toHaveBeenCalledWith({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load inventory items'
      });
      expect(component.loading).toBeFalse();
    }));

    it('should handle empty item list', fakeAsync(() => {
      inventoryServiceSpy.getItems.and.returnValue(of(mockEmptyListResult));
      fixture.detectChanges();
      tick();

      expect(component.items.length).toBe(0);
      expect(component.totalRecords).toBe(0);
    }));
  });

  describe('Opening Add Dialog', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should open add dialog with empty item', () => {
      component.showAddDialog();

      expect(component.displayDialog).toBeTrue();
      expect(component.isEditMode).toBeFalse();
      expect(component.selectedItem.id).toBeUndefined();
      expect(component.selectedItem.name).toBe('');
      expect(component.selectedItem.sku).toBe('');
    });

    it('should reset selected item to defaults when opening add dialog', () => {
      // First set some values
      component.selectedItem = mockInventoryItem;
      component.isEditMode = true;

      component.showAddDialog();

      expect(component.selectedItem.name).toBe('');
      expect(component.selectedItem.quantity).toBe(0);
      expect(component.selectedItem.status).toBe(InventoryStatus.IN_STOCK);
    });

    it('should have default status as IN_STOCK for new item', () => {
      component.showAddDialog();

      expect(component.selectedItem.status).toBe(InventoryStatus.IN_STOCK);
    });
  });

  describe('Opening Edit Dialog', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should open edit dialog with selected item', () => {
      component.showEditDialog(mockInventoryItem);

      expect(component.displayDialog).toBeTrue();
      expect(component.isEditMode).toBeTrue();
      expect(component.selectedItem.id).toBe(mockInventoryItem.id);
      expect(component.selectedItem.name).toBe(mockInventoryItem.name);
    });

    it('should copy item data when editing', () => {
      component.showEditDialog(mockInventoryItem);

      expect(component.selectedItem.sku).toBe('TEST-001');
      expect(component.selectedItem.quantity).toBe(100);
      expect(component.selectedItem.unitPrice).toBe(29.99);
    });

    it('should set categoryId from category object', () => {
      component.showEditDialog(mockInventoryItem);

      expect(component.selectedItem.categoryId).toBe(mockInventoryItem.category?.id);
    });

    it('should set locationId from location object', () => {
      component.showEditDialog(mockInventoryItem);

      expect(component.selectedItem.locationId).toBe(mockInventoryItem.location?.id);
    });

    it('should handle item without category', () => {
      component.showEditDialog(mockInventoryItem2);

      expect(component.selectedItem.categoryId).toBeNull();
    });

    it('should handle item without location', () => {
      component.showEditDialog(mockInventoryItem2);

      expect(component.selectedItem.locationId).toBeNull();
    });
  });

  describe('Delete Confirmation', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should show confirmation dialog when deleting item', () => {
      component.deleteItem(mockInventoryItem);

      expect(confirmationServiceSpy.confirm).toHaveBeenCalled();
      const confirmCall = confirmationServiceSpy.confirm.calls.mostRecent();
      expect(confirmCall.args[0].message).toContain(mockInventoryItem.name);
    });

    it('should call delete service when confirmed', fakeAsync(() => {
      inventoryServiceSpy.deleteItem.and.returnValue(of('Item deleted successfully'));

      let acceptCallback: (() => void) | undefined;
      confirmationServiceSpy.confirm.and.callFake((config: { accept?: () => void }) => {
        acceptCallback = config.accept;
        return confirmationServiceSpy;
      });

      component.deleteItem(mockInventoryItem);

      expect(acceptCallback).toBeDefined();
      acceptCallback!();
      tick();

      expect(inventoryServiceSpy.deleteItem).toHaveBeenCalledWith(mockInventoryItem.id);
    }));

    it('should show success message after successful delete', fakeAsync(() => {
      inventoryServiceSpy.deleteItem.and.returnValue(of('Item deleted successfully'));

      let acceptCallback: (() => void) | undefined;
      confirmationServiceSpy.confirm.and.callFake((config: { accept?: () => void }) => {
        acceptCallback = config.accept;
        return confirmationServiceSpy;
      });

      component.deleteItem(mockInventoryItem);
      acceptCallback!();
      tick();

      expect(messageServiceSpy.add).toHaveBeenCalledWith({
        severity: 'success',
        summary: 'Success',
        detail: 'Item deleted successfully'
      });
    }));

    it('should reload items after successful delete', fakeAsync(() => {
      inventoryServiceSpy.deleteItem.and.returnValue(of('Item deleted successfully'));
      inventoryServiceSpy.getItems.calls.reset();

      let acceptCallback: (() => void) | undefined;
      confirmationServiceSpy.confirm.and.callFake((config: { accept?: () => void }) => {
        acceptCallback = config.accept;
        return confirmationServiceSpy;
      });

      component.deleteItem(mockInventoryItem);
      acceptCallback!();
      tick();

      expect(inventoryServiceSpy.getItems).toHaveBeenCalled();
    }));

    it('should show error message when delete fails', fakeAsync(() => {
      inventoryServiceSpy.deleteItem.and.returnValue(throwError(() => new Error('Delete failed')));

      let acceptCallback: (() => void) | undefined;
      confirmationServiceSpy.confirm.and.callFake((config: { accept?: () => void }) => {
        acceptCallback = config.accept;
        return confirmationServiceSpy;
      });

      component.deleteItem(mockInventoryItem);
      acceptCallback!();
      tick();

      expect(messageServiceSpy.add).toHaveBeenCalledWith({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to delete item'
      });
    }));

    it('should not call delete service if item has no id', fakeAsync(() => {
      const itemWithoutId: IInventoryItem = {
        ...mockInventoryItem,
        id: undefined
      };

      let acceptCallback: (() => void) | undefined;
      confirmationServiceSpy.confirm.and.callFake((config: { accept?: () => void }) => {
        acceptCallback = config.accept;
        return confirmationServiceSpy;
      });

      component.deleteItem(itemWithoutId);
      acceptCallback!();
      tick();

      expect(inventoryServiceSpy.deleteItem).not.toHaveBeenCalled();
    }));
  });

  describe('Save Item', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should call createItem when saving new item', fakeAsync(() => {
      const newItem: IInventoryItem = {
        name: 'New Product',
        sku: 'NEW-001',
        quantity: 10,
        reorderPoint: 5,
        unitPrice: 19.99,
        status: InventoryStatus.IN_STOCK
      };

      inventoryServiceSpy.createItem.and.returnValue(of({ ...newItem, id: 'new-id' }));

      component.showAddDialog();
      component.selectedItem = newItem;
      component.saveItem();
      tick();

      expect(inventoryServiceSpy.createItem).toHaveBeenCalledWith(newItem);
    }));

    it('should call updateItem when saving existing item', fakeAsync(() => {
      inventoryServiceSpy.updateItem.and.returnValue(of(mockInventoryItem));

      component.showEditDialog(mockInventoryItem);
      component.saveItem();
      tick();

      expect(inventoryServiceSpy.updateItem).toHaveBeenCalledWith(
        mockInventoryItem.id,
        jasmine.any(Object)
      );
    }));

    it('should close dialog after successful create', fakeAsync(() => {
      inventoryServiceSpy.createItem.and.returnValue(of({ ...mockInventoryItem, id: 'new-id' }));

      component.showAddDialog();
      component.selectedItem = mockInventoryItem;
      component.saveItem();
      tick();

      expect(component.displayDialog).toBeFalse();
    }));

    it('should show success message after create', fakeAsync(() => {
      inventoryServiceSpy.createItem.and.returnValue(of({ ...mockInventoryItem, id: 'new-id' }));

      component.showAddDialog();
      component.selectedItem = mockInventoryItem;
      component.saveItem();
      tick();

      expect(messageServiceSpy.add).toHaveBeenCalledWith({
        severity: 'success',
        summary: 'Success',
        detail: 'Item created successfully'
      });
    }));
  });

  describe('Filters', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should reset page to 1 on search', () => {
      component.currentPage = 3;
      component.searchTerm = 'test';

      component.onSearch();

      expect(component.currentPage).toBe(1);
    });

    it('should reset page to 1 on filter change', () => {
      component.currentPage = 2;
      component.selectedCategories = ['cat-1'];

      component.onFilterChange();

      expect(component.currentPage).toBe(1);
    });

    it('should clear all filters', () => {
      component.searchTerm = 'test';
      component.selectedCategories = ['cat-1'];
      component.selectedLocations = ['loc-1'];
      component.selectedStatuses = [InventoryStatus.LOW_STOCK];

      component.clearFilters();

      expect(component.searchTerm).toBe('');
      expect(component.selectedCategories).toEqual([]);
      expect(component.selectedLocations).toEqual([]);
      expect(component.selectedStatuses).toEqual([]);
    });

    it('should detect active filters', () => {
      expect(component.hasActiveFilters()).toBeFalse();

      component.searchTerm = 'test';
      expect(component.hasActiveFilters()).toBeTrue();

      component.searchTerm = '';
      component.selectedCategories = ['cat-1'];
      expect(component.hasActiveFilters()).toBeTrue();
    });
  });

  describe('Bulk Actions', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should not call bulk delete when no items selected', () => {
      component.selectedItems = [];
      component.bulkDelete();

      expect(confirmationServiceSpy.confirm).not.toHaveBeenCalled();
    });

    it('should show confirmation for bulk delete', () => {
      component.selectedItems = [mockInventoryItem, mockInventoryItem2];
      component.bulkDelete();

      expect(confirmationServiceSpy.confirm).toHaveBeenCalled();
      const confirmCall = confirmationServiceSpy.confirm.calls.mostRecent();
      expect(confirmCall.args[0].message).toContain('2 item(s)');
    });

    it('should call bulk delete service when confirmed', fakeAsync(() => {
      component.selectedItems = [mockInventoryItem, mockInventoryItem2];
      inventoryServiceSpy.bulkDelete.and.returnValue(of({
        successCount: 2,
        failedCount: 0,
        failedIds: []
      }));

      let acceptCallback: (() => void) | undefined;
      confirmationServiceSpy.confirm.and.callFake((config: { accept?: () => void }) => {
        acceptCallback = config.accept;
        return confirmationServiceSpy;
      });

      component.bulkDelete();
      acceptCallback!();
      tick();

      expect(inventoryServiceSpy.bulkDelete).toHaveBeenCalledWith([
        mockInventoryItem.id,
        mockInventoryItem2.id
      ]);
    }));

    it('should clear selection after bulk delete', fakeAsync(() => {
      component.selectedItems = [mockInventoryItem];
      inventoryServiceSpy.bulkDelete.and.returnValue(of({
        successCount: 1,
        failedCount: 0,
        failedIds: []
      }));

      let acceptCallback: (() => void) | undefined;
      confirmationServiceSpy.confirm.and.callFake((config: { accept?: () => void }) => {
        acceptCallback = config.accept;
        return confirmationServiceSpy;
      });

      component.bulkDelete();
      acceptCallback!();
      tick();

      expect(component.selectedItems).toEqual([]);
    }));

    it('should not call bulk status update when no items selected', () => {
      component.selectedItems = [];
      component.bulkStatusChange(InventoryStatus.ON_ORDER);

      expect(inventoryServiceSpy.bulkStatusUpdate).not.toHaveBeenCalled();
    });

    it('should call bulk status update with correct parameters', fakeAsync(() => {
      component.selectedItems = [mockInventoryItem];
      inventoryServiceSpy.bulkStatusUpdate.and.returnValue(of({
        successCount: 1,
        failedCount: 0,
        failedIds: []
      }));

      component.bulkStatusChange(InventoryStatus.DISCONTINUED);
      tick();

      expect(inventoryServiceSpy.bulkStatusUpdate).toHaveBeenCalledWith(
        [mockInventoryItem.id],
        InventoryStatus.DISCONTINUED
      );
    }));
  });

  describe('Utility Methods', () => {
    it('should return correct status label', () => {
      expect(component.getStatusLabel(InventoryStatus.IN_STOCK)).toBe('In Stock');
      expect(component.getStatusLabel(InventoryStatus.LOW_STOCK)).toBe('Low Stock');
      expect(component.getStatusLabel(InventoryStatus.OUT_OF_STOCK)).toBe('Out of Stock');
      expect(component.getStatusLabel(InventoryStatus.ON_ORDER)).toBe('On Order');
      expect(component.getStatusLabel(InventoryStatus.DISCONTINUED)).toBe('Discontinued');
    });

    it('should return correct row class for status', () => {
      expect(component.getRowClass({ ...mockInventoryItem, status: InventoryStatus.IN_STOCK }))
        .toBe('row-in-stock');
      expect(component.getRowClass({ ...mockInventoryItem, status: InventoryStatus.LOW_STOCK }))
        .toBe('row-low-stock');
      expect(component.getRowClass({ ...mockInventoryItem, status: InventoryStatus.OUT_OF_STOCK }))
        .toBe('row-out-of-stock');
    });

    it('should return empty item with correct defaults', () => {
      const emptyItem = component.getEmptyItem();

      expect(emptyItem.name).toBe('');
      expect(emptyItem.sku).toBe('');
      expect(emptyItem.quantity).toBe(0);
      expect(emptyItem.reorderPoint).toBe(0);
      expect(emptyItem.unitPrice).toBe(0);
      expect(emptyItem.status).toBe(InventoryStatus.IN_STOCK);
      expect(emptyItem.categoryId).toBeNull();
      expect(emptyItem.locationId).toBeNull();
    });
  });

  describe('Navigation', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should navigate to item detail', () => {
      component.viewItemDetail(mockInventoryItem);

      expect(routerSpy.navigate).toHaveBeenCalledWith(['/inventory', mockInventoryItem.id]);
    });

    it('should not navigate if item has no id', () => {
      const itemWithoutId: IInventoryItem = {
        ...mockInventoryItem,
        id: undefined
      };

      component.viewItemDetail(itemWithoutId);

      expect(routerSpy.navigate).not.toHaveBeenCalled();
    });
  });

  describe('Quick Adjust', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should open quick adjust dialog', () => {
      component.showQuickAdjustDialog(mockInventoryItem);

      expect(component.displayQuickAdjustDialog).toBeTrue();
      expect(component.quickAdjustItem).toEqual(mockInventoryItem);
      expect(component.quickAdjustQuantity).toBe(mockInventoryItem.quantity);
      expect(component.quickAdjustReason).toBe('');
    });

    it('should save quick adjustment', fakeAsync(() => {
      inventoryServiceSpy.quickAdjust.and.returnValue(of({
        ...mockInventoryItem,
        quantity: 150
      }));

      component.showQuickAdjustDialog(mockInventoryItem);
      component.quickAdjustQuantity = 150;
      component.quickAdjustReason = 'Stock replenishment';
      component.saveQuickAdjust();
      tick();

      expect(inventoryServiceSpy.quickAdjust).toHaveBeenCalledWith(
        mockInventoryItem.id,
        150,
        'Stock replenishment'
      );
      expect(component.displayQuickAdjustDialog).toBeFalse();
    }));

    it('should not save if no item selected', () => {
      component.quickAdjustItem = null;
      component.saveQuickAdjust();

      expect(inventoryServiceSpy.quickAdjust).not.toHaveBeenCalled();
    });
  });

  describe('Detail Dialog', () => {
    beforeEach(fakeAsync(() => {
      fixture.detectChanges();
      tick();
    }));

    it('should open detail dialog', () => {
      inventoryServiceSpy.getItemLocationQuantities.and.returnValue(of({
        items: [],
        pagination: mockPaginationMeta
      }));

      component.showDetailDialog(mockInventoryItem);

      expect(component.displayDetailDialog).toBeTrue();
      expect(component.detailItem).toEqual(mockInventoryItem);
      expect(component.loadingDetail).toBeTrue();
    });

    it('should load location quantities for detail', fakeAsync(() => {
      const mockQuantities = [
        {
          inventoryItemId: mockInventoryItem.id!,
          locationId: '550e8400-e29b-41d4-a716-446655440020',
          quantity: 100,
          binLocation: 'A1'
        }
      ];

      inventoryServiceSpy.getItemLocationQuantities.and.returnValue(of({
        items: mockQuantities,
        pagination: mockPaginationMeta
      }));

      component.showDetailDialog(mockInventoryItem);
      tick();

      expect(inventoryServiceSpy.getItemLocationQuantities).toHaveBeenCalledWith(mockInventoryItem.id);
      expect(component.locationQuantities.length).toBe(1);
      expect(component.loadingDetail).toBeFalse();
    }));
  });
});
