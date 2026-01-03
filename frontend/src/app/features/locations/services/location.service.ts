import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ILocation } from '../models/location.model';
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

  getLocations(page: number = 1, pageSize: number = 25, isActive?: boolean): Observable<ILocationListResult> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    if (isActive !== undefined) {
      params = params.set('isActive', isActive.toString());
    }

    return this.http.get<IListResponse<ILocation>>(this.apiUrl, { params })
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  getLocation(id: string): Observable<ILocation> {
    return this.http.get<IDataResponse<ILocation>>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.data));
  }

  createLocation(location: ILocation): Observable<ILocation> {
    return this.http.post<IDataResponse<ILocation>>(this.apiUrl, location)
      .pipe(map(response => response.data));
  }

  updateLocation(id: string, location: Partial<ILocation>): Observable<ILocation> {
    return this.http.put<IDataResponse<ILocation>>(`${this.apiUrl}/${id}`, location)
      .pipe(map(response => response.data));
  }

  deleteLocation(id: string): Observable<string> {
    return this.http.delete<IMessageResponse>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.message));
  }
}
