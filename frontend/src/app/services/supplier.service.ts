import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { ISupplier, ISupplierCreate, ISupplierUpdate } from '../models/supplier.model';

interface ApiResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
}

interface ListResponse<T> {
  data: T[];
  meta: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

@Injectable({ providedIn: 'root' })
export class SupplierService {
  private readonly apiUrl = `${environment.apiUrl}/suppliers`;

  constructor(private http: HttpClient) {}

  getSuppliers(
    page: number = 1,
    pageSize: number = 50,
    search?: string
  ): Observable<{ items: ISupplier[]; total: number; page: number; pageSize: number }> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (search) params = params.set('search', search);

    return this.http.get<ListResponse<ISupplier>>(this.apiUrl + '/', { params }).pipe(
      map((resp) => ({
        items: resp.data,
        total: resp.meta.totalItems,
        page: resp.meta.page,
        pageSize: resp.meta.pageSize,
      }))
    );
  }

  getById(id: string): Observable<ISupplier> {
    return this.http
      .get<ApiResponse<ISupplier>>(`${this.apiUrl}/${id}`)
      .pipe(map((resp) => resp.data));
  }

  create(data: ISupplierCreate): Observable<ISupplier> {
    return this.http
      .post<ApiResponse<ISupplier>>(this.apiUrl + '/', data)
      .pipe(map((resp) => resp.data));
  }

  update(id: string, data: ISupplierUpdate): Observable<ISupplier> {
    return this.http
      .put<ApiResponse<ISupplier>>(`${this.apiUrl}/${id}`, data)
      .pipe(map((resp) => resp.data));
  }

  delete(id: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiUrl}/${id}`);
  }
}
