import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';

interface ApiResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
}

export interface IReorderSuggestion {
  itemId: string;
  sku: string;
  name: string;
  currentStock: number;
  reorderPoint: number;
  expectedDemand: number;
  leadTimeDays: number;
  recommendedOrderQuantity: number;
  recommendedOrderDate: string | null;
  rationale: string;
}

export interface IDailyForecast {
  forecastDate: string; // ISO date
  quantity: number;
  method: string;
}

@Injectable({ providedIn: 'root' })
export class ForecastingService {
  private readonly apiUrl = `${environment.apiUrl}/forecast`;

  constructor(private http: HttpClient) {}

  getReorderSuggestions(leadTimeDays: number = 7): Observable<IReorderSuggestion[]> {
    const params = new HttpParams().set('lead_time_days', String(leadTimeDays));
    return this.http
      .get<ApiResponse<IReorderSuggestion[]>>(this.apiUrl + '/reorder-suggestions', { params })
      .pipe(map((resp) => resp.data));
  }

  runMovingAverage(itemId: string, windowSize: number = 7, periods: number = 14): Observable<IDailyForecast[]> {
    const params = new HttpParams()
      .set('method', 'moving_average')
      .set('window_size', String(windowSize))
      .set('periods', String(periods));
    return this.http
      .post<ApiResponse<IDailyForecast[]>>(`${this.apiUrl}/items/${itemId}`, null, { params })
      .pipe(map((resp) => resp.data));
  }

  runExpSmoothing(
    itemId: string,
    windowSize: number = 7,
    periods: number = 14,
    alpha: number = 0.3
  ): Observable<IDailyForecast[]> {
    const params = new HttpParams()
      .set('method', 'exp_smoothing')
      .set('window_size', String(windowSize))
      .set('periods', String(periods))
      .set('alpha', String(alpha));
    return this.http
      .post<ApiResponse<IDailyForecast[]>>(`${this.apiUrl}/items/${itemId}`, null, { params })
      .pipe(map((resp) => resp.data));
  }
}
