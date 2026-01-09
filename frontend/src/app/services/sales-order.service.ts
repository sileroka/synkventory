import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import {
  ISalesOrderListItem,
  ISalesOrderDetail,
  ISalesOrderCreate,
  ISalesOrderUpdate,
  IShipItemsRequest,
  IListQuery,
  IListResult,
  SalesOrderStatus,
} from '../models/sales-order.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class SalesOrderService {
  private baseUrl = `${environment.apiUrl}/sales-orders`;

  constructor(private http: HttpClient) {}

  async list(query: IListQuery = {}): Promise<IListResult<ISalesOrderListItem>> {
    let params = new HttpParams();
    if (query.page) params = params.set('page', query.page);
    if (query.pageSize) params = params.set('pageSize', query.pageSize);
    if (query.search) params = params.set('search', query.search);
    if (query.status) params = params.set('status', query.status);
    if (query.customerId) params = params.set('customerId', query.customerId);

    const res = await firstValueFrom(this.http.get<any>(this.baseUrl, { params, withCredentials: true }));
    const items = (res?.data ?? []) as ISalesOrderListItem[];
    const total = res?.meta?.totalItems ?? items.length;
    return { items, total };
  }

  async get(id: string): Promise<ISalesOrderDetail> {
    const res = await firstValueFrom(this.http.get<any>(`${this.baseUrl}/${id}`, { withCredentials: true }));
    return res?.data as ISalesOrderDetail;
  }

  async create(payload: ISalesOrderCreate): Promise<ISalesOrderDetail> {
    const res = await firstValueFrom(this.http.post<any>(this.baseUrl, payload, { withCredentials: true }));
    return res?.data as ISalesOrderDetail;
  }

  async update(id: string, payload: ISalesOrderUpdate): Promise<ISalesOrderDetail> {
    const res = await firstValueFrom(this.http.put<any>(`${this.baseUrl}/${id}`, payload, { withCredentials: true }));
    return res?.data as ISalesOrderDetail;
  }

  async changeStatus(id: string, status: SalesOrderStatus): Promise<ISalesOrderDetail> {
    const res = await firstValueFrom(
      this.http.put<any>(`${this.baseUrl}/${id}/status`, { status }, { withCredentials: true })
    );
    return res?.data as ISalesOrderDetail;
  }

  async addLineItem(id: string, item: { itemId: string; quantity: number; unitPrice?: number }): Promise<ISalesOrderDetail> {
    const res = await firstValueFrom(
      this.http.post<any>(`${this.baseUrl}/${id}/line-items`, item, { withCredentials: true })
    );
    return res?.data as ISalesOrderDetail;
  }

  async removeLineItem(id: string, lineItemId: string): Promise<ISalesOrderDetail> {
    const res = await firstValueFrom(
      this.http.delete<any>(`${this.baseUrl}/${id}/line-items/${lineItemId}`, { withCredentials: true })
    );
    return res?.data as ISalesOrderDetail;
  }

  async ship(id: string, payload: IShipItemsRequest): Promise<ISalesOrderDetail> {
    const res = await firstValueFrom(
      this.http.post<any>(`${this.baseUrl}/${id}/ship`, payload, { withCredentials: true })
    );
    return res?.data as ISalesOrderDetail;
  }
}
