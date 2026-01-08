import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  IItemLot,
  IItemLotCreate,
  IItemLotUpdate,
  IItemLotListResult,
  ILotFilters
} from '../models/item-lot.model';
import { IDataResponse, IListResponse, IMessageResponse } from '../models/api-response.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ItemLotService {
  private apiUrl = `${environment.apiUrl}/inventory`;
  private lotsUrl = `${environment.apiUrl}/inventory/lots`;

  constructor(private http: HttpClient) { }

  /**
   * Get lots for a specific inventory item
   */
  getLotsForItem(
    itemId: string,
    page: number = 1,
    pageSize: number = 25,
    filters?: ILotFilters
  ): Observable<IListResponse<IItemLot>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    if (filters) {
      if (filters.locationId) {
        params = params.set('locationId', filters.locationId);
      }
      if (filters.includeExpired !== undefined) {
        params = params.set('includeExpired', filters.includeExpired.toString());
      }
      if (filters.orderBy) {
        params = params.set('orderBy', filters.orderBy);
      }
    }

    return this.http.get<IListResponse<IItemLot>>(
      `${this.apiUrl}/items/${itemId}/lots`,
      { params }
    );
  }

  /**
   * Get a specific lot by ID
   */
  getLotById(lotId: string): Observable<IDataResponse<IItemLot>> {
    return this.http.get<IDataResponse<IItemLot>>(
      `${this.lotsUrl}/${lotId}`
    );
  }

  /**
   * Create a new lot for an item
   */
  createLot(itemId: string, lot: IItemLotCreate): Observable<IDataResponse<IItemLot>> {
    return this.http.post<IDataResponse<IItemLot>>(
      `${this.apiUrl}/items/${itemId}/lots`,
      lot
    );
  }

  /**
   * Update an existing lot
   */
  updateLot(lotId: string, updates: IItemLotUpdate): Observable<IDataResponse<IItemLot>> {
    return this.http.put<IDataResponse<IItemLot>>(
      `${this.lotsUrl}/${lotId}`,
      updates
    );
  }

  /**
   * Delete a lot
   */
  deleteLot(lotId: string): Observable<IMessageResponse> {
    return this.http.delete<IMessageResponse>(
      `${this.lotsUrl}/${lotId}`
    );
  }

  /**
   * Check if lot number is unique
   */
  isLotNumberUnique(itemId: string, lotNumber: string, excludeLotId?: string): Observable<{ unique: boolean }> {
    let params = new HttpParams()
      .set('itemId', itemId)
      .set('lotNumber', lotNumber);

    if (excludeLotId) {
      params = params.set('excludeLotId', excludeLotId);
    }

    return this.http.get<{ unique: boolean }>(
      `${this.lotsUrl}/validate/unique`,
      { params }
    );
  }
}
