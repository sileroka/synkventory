import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { InventoryService, IInventoryFilters, IBulkOperationResult } from './inventory.service';
import { IInventoryItem, InventoryStatus, ILowStockAlert } from '../models/inventory-item.model';
import { IDataResponse, IListResponse, IMessageResponse, IPaginationMeta } from '../models/api-response.model';
import { IStockMovement, MovementType } from '../models/stock-movement.model';

describe('InventoryService', () => {
  let service: InventoryService;
  let httpMock: HttpTestingController;

  const API_URL = 'http://localhost:8000/api/v1/inventory';

  // Mock data matching IInventoryItem interface
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

  const mockPaginationMeta: IPaginationMeta = {
    page: 1,
    pageSize: 25,
    totalItems: 2,
    totalPages: 1,
    timestamp: '2026-01-01T00:00:00Z',
    requestId: 'test-request-id'
  };

  const mockResponseMeta = {
    timestamp: '2026-01-01T00:00:00Z',
    requestId: 'test-request-id'
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [InventoryService]
    });

    service = TestBed.inject(InventoryService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getItems', () => {
    it('should return inventory items with pagination', () => {
      const mockResponse: IListResponse<IInventoryItem> = {
        data: [mockInventoryItem, mockInventoryItem2],
        meta: mockPaginationMeta
      };

      service.getItems(1, 25).subscribe(result => {
        expect(result.items.length).toBe(2);
        expect(result.items[0]).toEqual(mockInventoryItem);
        expect(result.pagination.totalItems).toBe(2);
      });

      const req = httpMock.expectOne(`${API_URL}?page=1&pageSize=25`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should include search filter in request params', () => {
      const filters: IInventoryFilters = { search: 'widget' };
      const mockResponse: IListResponse<IInventoryItem> = {
        data: [mockInventoryItem],
        meta: { ...mockPaginationMeta, totalItems: 1 }
      };

      service.getItems(1, 25, filters).subscribe(result => {
        expect(result.items.length).toBe(1);
      });

      const req = httpMock.expectOne(`${API_URL}?page=1&pageSize=25&search=widget`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should include category filter in request params', () => {
      const filters: IInventoryFilters = { categoryIds: ['cat-1', 'cat-2'] };
      const mockResponse: IListResponse<IInventoryItem> = {
        data: [],
        meta: { ...mockPaginationMeta, totalItems: 0 }
      };

      service.getItems(1, 25, filters).subscribe(result => {
        expect(result.items).toEqual([]);
      });

      const req = httpMock.expectOne(r => r.url === API_URL && r.params.getAll('categoryIds')?.length === 2);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.getAll('categoryIds')).toEqual(['cat-1', 'cat-2']);
      req.flush(mockResponse);
    });

    it('should include location filter in request params', () => {
      const filters: IInventoryFilters = { locationIds: ['loc-1'] };
      const mockResponse: IListResponse<IInventoryItem> = {
        data: [],
        meta: { ...mockPaginationMeta, totalItems: 0 }
      };

      service.getItems(1, 25, filters).subscribe();

      const req = httpMock.expectOne(r => r.url === API_URL && r.params.get('locationIds') === 'loc-1');
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should include status filter in request params', () => {
      const filters: IInventoryFilters = { statuses: [InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK] };
      const mockResponse: IListResponse<IInventoryItem> = {
        data: [mockInventoryItem2],
        meta: { ...mockPaginationMeta, totalItems: 1 }
      };

      service.getItems(1, 25, filters).subscribe();

      const req = httpMock.expectOne(r => r.url === API_URL && r.params.getAll('statuses')?.length === 2);
      expect(req.request.params.getAll('statuses')).toEqual([InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK]);
      req.flush(mockResponse);
    });

    it('should include sorting in request params', () => {
      const filters: IInventoryFilters = { sortField: 'name', sortOrder: -1 };
      const mockResponse: IListResponse<IInventoryItem> = {
        data: [mockInventoryItem2, mockInventoryItem],
        meta: mockPaginationMeta
      };

      service.getItems(1, 25, filters).subscribe();

      const req = httpMock.expectOne(r =>
        r.url === API_URL &&
        r.params.get('sortField') === 'name' &&
        r.params.get('sortOrder') === '-1'
      );
      req.flush(mockResponse);
    });
  });

  describe('getItem', () => {
    it('should return a single inventory item by ID', () => {
      const mockResponse: IDataResponse<IInventoryItem> = {
        data: mockInventoryItem,
        meta: mockResponseMeta
      };

      service.getItem(mockInventoryItem.id!).subscribe(item => {
        expect(item).toEqual(mockInventoryItem);
        expect(item.name).toBe('Test Widget');
        expect(item.sku).toBe('TEST-001');
      });

      const req = httpMock.expectOne(`${API_URL}/${mockInventoryItem.id}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('getItemLocationQuantities', () => {
    it('should return location quantities for an item', () => {
      const mockLocationQuantities = [
        {
          inventoryItemId: mockInventoryItem.id!,
          locationId: '550e8400-e29b-41d4-a716-446655440020',
          quantity: 50,
          binLocation: 'A1-B2',
          location: { id: '550e8400-e29b-41d4-a716-446655440020', name: 'Warehouse A' }
        },
        {
          inventoryItemId: mockInventoryItem.id!,
          locationId: '550e8400-e29b-41d4-a716-446655440021',
          quantity: 50,
          binLocation: 'C3-D4',
          location: { id: '550e8400-e29b-41d4-a716-446655440021', name: 'Warehouse B' }
        }
      ];

      const mockResponse: IListResponse<typeof mockLocationQuantities[0]> = {
        data: mockLocationQuantities,
        meta: { ...mockPaginationMeta, totalItems: 2 }
      };

      service.getItemLocationQuantities(mockInventoryItem.id!).subscribe(result => {
        expect(result.items.length).toBe(2);
        expect(result.items[0].quantity).toBe(50);
        expect(result.items[0].binLocation).toBe('A1-B2');
      });

      const req = httpMock.expectOne(`${API_URL}/${mockInventoryItem.id}/locations`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('createItem', () => {
    it('should create a new inventory item', () => {
      const newItem: IInventoryItem = {
        name: 'New Product',
        sku: 'NEW-001',
        quantity: 50,
        reorderPoint: 5,
        unitPrice: 19.99,
        status: InventoryStatus.IN_STOCK
      };

      const createdItem: IInventoryItem = {
        ...newItem,
        id: '550e8400-e29b-41d4-a716-446655440099',
        createdAt: '2026-01-02T00:00:00Z',
        updatedAt: '2026-01-02T00:00:00Z'
      };

      const mockResponse: IDataResponse<IInventoryItem> = {
        data: createdItem,
        meta: mockResponseMeta
      };

      service.createItem(newItem).subscribe(item => {
        expect(item.id).toBeTruthy();
        expect(item.name).toBe('New Product');
        expect(item.sku).toBe('NEW-001');
      });

      const req = httpMock.expectOne(API_URL);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(newItem);
      req.flush(mockResponse);
    });
  });

  describe('updateItem', () => {
    it('should update an existing inventory item', () => {
      const updates: Partial<IInventoryItem> = {
        name: 'Updated Widget',
        quantity: 150
      };

      const updatedItem: IInventoryItem = {
        ...mockInventoryItem,
        ...updates,
        updatedAt: '2026-01-02T12:00:00Z'
      };

      const mockResponse: IDataResponse<IInventoryItem> = {
        data: updatedItem,
        meta: mockResponseMeta
      };

      service.updateItem(mockInventoryItem.id!, updates).subscribe(item => {
        expect(item.name).toBe('Updated Widget');
        expect(item.quantity).toBe(150);
      });

      const req = httpMock.expectOne(`${API_URL}/${mockInventoryItem.id}`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(updates);
      req.flush(mockResponse);
    });

    it('should update item status', () => {
      const updates: Partial<IInventoryItem> = {
        status: InventoryStatus.DISCONTINUED
      };

      const updatedItem: IInventoryItem = {
        ...mockInventoryItem,
        ...updates
      };

      const mockResponse: IDataResponse<IInventoryItem> = {
        data: updatedItem,
        meta: mockResponseMeta
      };

      service.updateItem(mockInventoryItem.id!, updates).subscribe(item => {
        expect(item.status).toBe(InventoryStatus.DISCONTINUED);
      });

      const req = httpMock.expectOne(`${API_URL}/${mockInventoryItem.id}`);
      req.flush(mockResponse);
    });
  });

  describe('deleteItem', () => {
    it('should delete an inventory item', () => {
      const mockResponse: IMessageResponse = {
        message: 'Item deleted successfully',
        meta: mockResponseMeta
      };

      service.deleteItem(mockInventoryItem.id!).subscribe(message => {
        expect(message).toBe('Item deleted successfully');
      });

      const req = httpMock.expectOne(`${API_URL}/${mockInventoryItem.id}`);
      expect(req.request.method).toBe('DELETE');
      req.flush(mockResponse);
    });
  });

  describe('bulkDelete', () => {
    it('should delete multiple inventory items', () => {
      const ids = [mockInventoryItem.id!, mockInventoryItem2.id!];
      const mockResult: IBulkOperationResult = {
        successCount: 2,
        failedCount: 0,
        failedIds: []
      };

      const mockResponse: IDataResponse<IBulkOperationResult> = {
        data: mockResult,
        meta: mockResponseMeta
      };

      service.bulkDelete(ids).subscribe(result => {
        expect(result.successCount).toBe(2);
        expect(result.failedCount).toBe(0);
        expect(result.failedIds).toEqual([]);
      });

      const req = httpMock.expectOne(`${API_URL}/bulk-delete`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ ids });
      req.flush(mockResponse);
    });

    it('should handle partial bulk delete failure', () => {
      const ids = [mockInventoryItem.id!, 'non-existent-id'];
      const mockResult: IBulkOperationResult = {
        successCount: 1,
        failedCount: 1,
        failedIds: ['non-existent-id']
      };

      const mockResponse: IDataResponse<IBulkOperationResult> = {
        data: mockResult,
        meta: mockResponseMeta
      };

      service.bulkDelete(ids).subscribe(result => {
        expect(result.successCount).toBe(1);
        expect(result.failedCount).toBe(1);
        expect(result.failedIds).toContain('non-existent-id');
      });

      const req = httpMock.expectOne(`${API_URL}/bulk-delete`);
      req.flush(mockResponse);
    });
  });

  describe('bulkStatusUpdate', () => {
    it('should update status for multiple items', () => {
      const ids = [mockInventoryItem.id!, mockInventoryItem2.id!];
      const newStatus = InventoryStatus.ON_ORDER;
      const mockResult: IBulkOperationResult = {
        successCount: 2,
        failedCount: 0,
        failedIds: []
      };

      const mockResponse: IDataResponse<IBulkOperationResult> = {
        data: mockResult,
        meta: mockResponseMeta
      };

      service.bulkStatusUpdate(ids, newStatus).subscribe(result => {
        expect(result.successCount).toBe(2);
      });

      const req = httpMock.expectOne(`${API_URL}/bulk-status-update`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ ids, status: newStatus });
      req.flush(mockResponse);
    });
  });

  describe('quickAdjust', () => {
    it('should adjust item quantity', () => {
      const adjustedItem: IInventoryItem = {
        ...mockInventoryItem,
        quantity: 120
      };

      const mockResponse: IDataResponse<IInventoryItem> = {
        data: adjustedItem,
        meta: mockResponseMeta
      };

      service.quickAdjust(mockInventoryItem.id!, 120, 'Stock replenishment').subscribe(item => {
        expect(item.quantity).toBe(120);
      });

      const req = httpMock.expectOne(`${API_URL}/${mockInventoryItem.id}/quick-adjust`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ quantity: 120, reason: 'Stock replenishment' });
      req.flush(mockResponse);
    });

    it('should adjust quantity without reason', () => {
      const adjustedItem: IInventoryItem = {
        ...mockInventoryItem,
        quantity: 80
      };

      const mockResponse: IDataResponse<IInventoryItem> = {
        data: adjustedItem,
        meta: mockResponseMeta
      };

      service.quickAdjust(mockInventoryItem.id!, 80).subscribe(item => {
        expect(item.quantity).toBe(80);
      });

      const req = httpMock.expectOne(`${API_URL}/${mockInventoryItem.id}/quick-adjust`);
      expect(req.request.body).toEqual({ quantity: 80, reason: undefined });
      req.flush(mockResponse);
    });
  });

  describe('getLowStockAlerts', () => {
    it('should return low stock alerts', () => {
      const mockAlerts: ILowStockAlert[] = [
        {
          id: mockInventoryItem2.id!,
          name: mockInventoryItem2.name,
          sku: mockInventoryItem2.sku,
          quantity: mockInventoryItem2.quantity,
          reorderPoint: mockInventoryItem2.reorderPoint,
          suggestedOrderQuantity: 15,
          status: InventoryStatus.LOW_STOCK,
          category: null,
          location: null
        }
      ];

      const mockResponse: IListResponse<ILowStockAlert> = {
        data: mockAlerts,
        meta: { ...mockPaginationMeta, totalItems: 1 }
      };

      service.getLowStockAlerts(1, 100).subscribe(result => {
        expect(result.items.length).toBe(1);
        expect(result.items[0].suggestedOrderQuantity).toBe(15);
      });

      const req = httpMock.expectOne(`${API_URL}/alerts/low-stock?page=1&pageSize=100`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('getItemMovements', () => {
    it('should return stock movements for an item', () => {
      const mockMovements: IStockMovement[] = [
        {
          id: '550e8400-e29b-41d4-a716-446655440100',
          inventoryItemId: mockInventoryItem.id!,
          movementType: MovementType.ADJUSTMENT,
          quantityChange: 20,
          quantityBefore: 80,
          quantityAfter: 100,
          reason: 'Stock count adjustment',
          createdAt: '2026-01-01T10:00:00Z'
        }
      ];

      const mockResponse: IListResponse<IStockMovement> = {
        data: mockMovements,
        meta: { ...mockPaginationMeta, totalItems: 1 }
      };

      service.getItemMovements(mockInventoryItem.id!, 1, 10).subscribe(result => {
        expect(result.items.length).toBe(1);
        expect(result.items[0].movementType).toBe(MovementType.ADJUSTMENT);
        expect(result.items[0].quantityChange).toBe(20);
      });

      const req = httpMock.expectOne(`${API_URL}/${mockInventoryItem.id}/movements?page=1&pageSize=10`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('createStockMovement', () => {
    it('should create a stock movement', () => {
      const newMovement = {
        inventoryItemId: mockInventoryItem.id!,
        movementType: MovementType.RECEIPT,
        quantityChange: 50,
        reason: 'New shipment received',
        referenceNumber: 'PO-12345'
      };

      const createdMovement: IStockMovement = {
        id: '550e8400-e29b-41d4-a716-446655440101',
        ...newMovement,
        quantityBefore: 100,
        quantityAfter: 150,
        createdAt: '2026-01-02T00:00:00Z'
      };

      const mockResponse: IDataResponse<IStockMovement> = {
        data: createdMovement,
        meta: mockResponseMeta
      };

      service.createStockMovement(newMovement).subscribe(movement => {
        expect(movement.id).toBeTruthy();
        expect(movement.quantityAfter).toBe(150);
      });

      const req = httpMock.expectOne('http://localhost:8000/api/v1/stock-movements');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(newMovement);
      req.flush(mockResponse);
    });
  });
});
