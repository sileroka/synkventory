import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  IBillOfMaterial,
  IBillOfMaterialCreate,
  IBillOfMaterialUpdate,
  IBOMAvailability,
  IBOMBuildRequest,
  IBOMBuildResult,
  IBOMUnbuildRequest,
  IBOMUnbuildResult,
  IWhereUsedEntry,
} from '../models/bill-of-material.model';
import {
  IDataResponse,
  IListResponse,
  IMessageResponse,
} from '../models/api-response.model';

@Injectable({
  providedIn: 'root'
})
export class BomService {
  private apiUrl = `${environment.apiUrl}/inventory`;

  constructor(private http: HttpClient) { }

  /**
   * Get all BOM components for an item.
   */
  getItemBom(itemId: string): Observable<IBillOfMaterial[]> {
    return this.http.get<IListResponse<IBillOfMaterial>>(
      `${this.apiUrl}/items/${itemId}/bom`
    ).pipe(
      map(response => response.data)
    );
  }

  /**
   * Add a component to an item's BOM.
   */
  addBomComponent(itemId: string, data: IBillOfMaterialCreate): Observable<IBillOfMaterial> {
    return this.http.post<IDataResponse<IBillOfMaterial>>(
      `${this.apiUrl}/items/${itemId}/bom`,
      data
    ).pipe(
      map(response => response.data)
    );
  }

  /**
   * Update a BOM component entry.
   */
  updateBomComponent(bomId: string, data: IBillOfMaterialUpdate): Observable<IBillOfMaterial> {
    return this.http.put<IDataResponse<IBillOfMaterial>>(
      `${this.apiUrl}/bom/${bomId}`,
      data
    ).pipe(
      map(response => response.data)
    );
  }

  /**
   * Remove a component from an item's BOM.
   */
  deleteBomComponent(bomId: string): Observable<string> {
    return this.http.delete<IMessageResponse>(
      `${this.apiUrl}/bom/${bomId}`
    ).pipe(
      map(response => response.message)
    );
  }

  /**
   * Get all assemblies where an item is used as a component.
   */
  getWhereUsed(itemId: string): Observable<IWhereUsedEntry[]> {
    return this.http.get<IListResponse<IWhereUsedEntry>>(
      `${this.apiUrl}/items/${itemId}/where-used`
    ).pipe(
      map(response => response.data)
    );
  }

  /**
   * Calculate how many assemblies can be built with current stock.
   */
  getBuildAvailability(itemId: string): Observable<IBOMAvailability> {
    return this.http.get<IDataResponse<IBOMAvailability>>(
      `${this.apiUrl}/items/${itemId}/bom/availability`
    ).pipe(
      map(response => response.data)
    );
  }

  /**
   * Build assemblies from components.
   */
  buildAssembly(itemId: string, request: IBOMBuildRequest): Observable<IBOMBuildResult> {
    return this.http.post<IDataResponse<IBOMBuildResult>>(
      `${this.apiUrl}/items/${itemId}/bom/build`,
      request
    ).pipe(
      map(response => response.data)
    );
  }

  /**
   * Disassemble items back into components.
   */
  unbuildAssembly(itemId: string, request: IBOMUnbuildRequest): Observable<IBOMUnbuildResult> {
    return this.http.post<IDataResponse<IBOMUnbuildResult>>(
      `${this.apiUrl}/items/${itemId}/bom/unbuild`,
      request
    ).pipe(
      map(response => response.data)
    );
  }
}
