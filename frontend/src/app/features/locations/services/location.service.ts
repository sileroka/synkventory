import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ILocation, ILocationTreeNode, ILocationTypeInfo, LocationType } from '../models/location.model';
import { environment } from '../../../../environments/environment';
import {
  IDataResponse,
  IListResponse,
  IMessageResponse,
  IPaginationMeta
} from '../../../models/api-response.model';

export interface ILocationListResult {
  items: ILocation[];
  pagination: IPaginationMeta;
}

@Injectable({
  providedIn: 'root'
})
export class LocationService {
  private apiUrl = `${environment.apiUrl}/locations`;

  constructor(private http: HttpClient) { }

  /**
   * Get all location types with hierarchy info
   */
  getLocationTypes(): Observable<ILocationTypeInfo[]> {
    return this.http.get<IDataResponse<ILocationTypeInfo[]>>(`${this.apiUrl}/types`)
      .pipe(map(response => response.data));
  }

  /**
   * Get locations as a hierarchical tree
   */
  getLocationTree(isActive?: boolean): Observable<ILocationTreeNode[]> {
    let params = new HttpParams();
    if (isActive !== undefined) {
      params = params.set('isActive', isActive.toString());
    }
    return this.http.get<IDataResponse<ILocationTreeNode[]>>(`${this.apiUrl}/tree`, { params })
      .pipe(map(response => response.data));
  }

  /**
   * Get locations with pagination and optional filters
   */
  getLocations(
    page: number = 1,
    pageSize: number = 25,
    isActive?: boolean,
    locationType?: LocationType,
    parentId?: string | null
  ): Observable<ILocationListResult> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    if (isActive !== undefined) {
      params = params.set('isActive', isActive.toString());
    }

    if (locationType) {
      params = params.set('locationType', locationType);
    }

    if (parentId !== undefined) {
      params = params.set('parentId', parentId === null ? 'null' : parentId);
    }

    return this.http.get<IListResponse<ILocation>>(this.apiUrl, { params })
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  /**
   * Get warehouses only (top-level locations)
   */
  getWarehouses(isActive?: boolean): Observable<ILocationListResult> {
    return this.getLocations(1, 1000, isActive, 'warehouse', null);
  }

  /**
   * Get children of a location
   */
  getLocationChildren(parentId: string, isActive?: boolean): Observable<ILocation[]> {
    let params = new HttpParams();
    if (isActive !== undefined) {
      params = params.set('isActive', isActive.toString());
    }
    return this.http.get<IListResponse<ILocation>>(`${this.apiUrl}/${parentId}/children`, { params })
      .pipe(map(response => response.data));
  }

  /**
   * Get a single location by ID
   */
  getLocation(id: string): Observable<ILocation> {
    return this.http.get<IDataResponse<ILocation>>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.data));
  }

  /**
   * Create a new location
   */
  createLocation(location: Partial<ILocation>): Observable<ILocation> {
    return this.http.post<IDataResponse<ILocation>>(this.apiUrl, location)
      .pipe(map(response => response.data));
  }

  /**
   * Update an existing location
   */
  updateLocation(id: string, location: Partial<ILocation>): Observable<ILocation> {
    return this.http.put<IDataResponse<ILocation>>(`${this.apiUrl}/${id}`, location)
      .pipe(map(response => response.data));
  }

  /**
   * Delete a location (cascades to children)
   */
  deleteLocation(id: string): Observable<string> {
    return this.http.delete<IMessageResponse>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.message));
  }
}
