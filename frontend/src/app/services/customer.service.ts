import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { ICustomer, ICustomerCreate, ICustomerUpdate } from '../models/customer.model';

interface ApiResponse<T> { data: T; meta?: Record<string, unknown>; }

@Injectable({ providedIn: 'root' })
export class CustomerService {
  private readonly apiUrl = `${environment.apiUrl}/customers`;
  constructor(private http: HttpClient) {}

  getCustomers(page: number = 1, pageSize: number = 25, search?: string): Observable<{ items: ICustomer[]; total: number }> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (search) params = params.set('search', search);
    return this.http.get<any>(`${this.apiUrl}/`, { params }).pipe(
      map(resp => ({ items: resp.data.items as ICustomer[], total: resp.data.total as number }))
    );
  }

  getById(id: string): Observable<ICustomer> {
    return this.http.get<ApiResponse<ICustomer>>(`${this.apiUrl}/${id}`).pipe(map(r => r.data));
  }

  create(payload: ICustomerCreate): Observable<ICustomer> {
    return this.http.post<ApiResponse<ICustomer>>(`${this.apiUrl}/`, payload).pipe(map(r => r.data));
  }

  update(id: string, payload: ICustomerUpdate): Observable<ICustomer> {
    return this.http.put<ApiResponse<ICustomer>>(`${this.apiUrl}/${id}`, payload).pipe(map(r => r.data));
  }

  delete(id: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiUrl}/${id}`);
  }
}
