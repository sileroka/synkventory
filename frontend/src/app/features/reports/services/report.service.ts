import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import {
  IInventoryValuationReport,
  IStockMovementReport,
  MovementType
} from '../models/report.model';
import { IDataResponse } from '../../../models/api-response.model';

@Injectable({
  providedIn: 'root'
})
export class ReportService {
  private apiUrl = 'http://localhost:8000/api/v1/reports';

  constructor(private http: HttpClient) {}

  getInventoryValuation(
    categoryIds?: string[],
    locationIds?: string[]
  ): Observable<IInventoryValuationReport> {
    let params = new HttpParams();

    if (categoryIds && categoryIds.length > 0) {
      categoryIds.forEach(id => {
        params = params.append('categoryIds', id);
      });
    }

    if (locationIds && locationIds.length > 0) {
      locationIds.forEach(id => {
        params = params.append('locationIds', id);
      });
    }

    return this.http
      .get<IDataResponse<IInventoryValuationReport>>(
        `${this.apiUrl}/inventory-valuation`,
        { params }
      )
      .pipe(map((response: IDataResponse<IInventoryValuationReport>) => response.data));
  }

  getStockMovementReport(
    startDate?: Date,
    endDate?: Date,
    itemIds?: string[],
    locationIds?: string[],
    movementTypes?: MovementType[]
  ): Observable<IStockMovementReport> {
    let params = new HttpParams();

    if (startDate) {
      params = params.set('startDate', this.formatDate(startDate));
    }

    if (endDate) {
      params = params.set('endDate', this.formatDate(endDate));
    }

    if (itemIds && itemIds.length > 0) {
      itemIds.forEach(id => {
        params = params.append('itemIds', id);
      });
    }

    if (locationIds && locationIds.length > 0) {
      locationIds.forEach(id => {
        params = params.append('locationIds', id);
      });
    }

    if (movementTypes && movementTypes.length > 0) {
      movementTypes.forEach(type => {
        params = params.append('movementTypes', type);
      });
    }

    return this.http
      .get<IDataResponse<IStockMovementReport>>(
        `${this.apiUrl}/stock-movements`,
        { params }
      )
      .pipe(map((response: IDataResponse<IStockMovementReport>) => response.data));
  }

  private formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
}
