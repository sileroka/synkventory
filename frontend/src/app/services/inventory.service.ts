import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { IInventoryItem } from '../models/inventory-item.model';

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private apiUrl = 'http://localhost:8000/api/v1/inventory';

  constructor(private http: HttpClient) { }

  getItems(): Observable<IInventoryItem[]> {
    return this.http.get<IInventoryItem[]>(this.apiUrl);
  }

  getItem(id: string): Observable<IInventoryItem> {
    return this.http.get<IInventoryItem>(`${this.apiUrl}/${id}`);
  }

  createItem(item: IInventoryItem): Observable<IInventoryItem> {
    return this.http.post<IInventoryItem>(this.apiUrl, item);
  }

  updateItem(id: string, item: Partial<IInventoryItem>): Observable<IInventoryItem> {
    return this.http.put<IInventoryItem>(`${this.apiUrl}/${id}`, item);
  }

  deleteItem(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }
}
