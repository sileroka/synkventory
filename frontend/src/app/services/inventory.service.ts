import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { IInventoryItem } from '../models/inventory-item.model';
import {
  IDataResponse,
  IListResponse,
  IMessageResponse,
  IPaginationMeta
} from '../models/api-response.model';

export interface IInventoryListResult {
  items: IInventoryItem[];
  pagination: IPaginationMeta;
}

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private apiUrl = 'http://localhost:8000/api/v1/inventory';

  constructor(private http: HttpClient) { }

  getItems(page: number = 1, pageSize: number = 25): Observable<IInventoryListResult> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    return this.http.get<IListResponse<IInventoryItem>>(this.apiUrl, { params })
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  getItem(id: string): Observable<IInventoryItem> {
    return this.http.get<IDataResponse<IInventoryItem>>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.data));
  }

  createItem(item: IInventoryItem): Observable<IInventoryItem> {
    return this.http.post<IDataResponse<IInventoryItem>>(this.apiUrl, item)
      .pipe(map(response => response.data));
  }

  updateItem(id: string, item: Partial<IInventoryItem>): Observable<IInventoryItem> {
    return this.http.put<IDataResponse<IInventoryItem>>(`${this.apiUrl}/${id}`, item)
      .pipe(map(response => response.data));
  }

  deleteItem(id: string): Observable<string> {
    return this.http.delete<IMessageResponse>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.message));
  }
}
