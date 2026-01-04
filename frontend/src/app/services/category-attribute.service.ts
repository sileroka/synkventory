import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  ICategoryAttribute,
  ICategoryAttributeCreate,
  ICategoryAttributeUpdate,
} from '../models/category-attribute.model';

export interface ICategoryAttributeListResponse {
  items: ICategoryAttribute[];
}

@Injectable({
  providedIn: 'root',
})
export class CategoryAttributeService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}`;

  /**
   * Get all attributes for a category.
   */
  getAttributesByCategory(
    categoryId: string,
    includeInactive = false
  ): Observable<ICategoryAttributeListResponse> {
    let params = new HttpParams();
    if (includeInactive) {
      params = params.set('include_inactive', 'true');
    }
    return this.http.get<ICategoryAttribute[]>(
      `${this.apiUrl}/categories/${categoryId}/attributes`,
      { params, withCredentials: true }
    ).pipe(
      map(items => ({ items }))
    );
  }

  /**
   * Get a single attribute by ID.
   */
  getAttribute(attributeId: string): Observable<ICategoryAttribute> {
    return this.http.get<ICategoryAttribute>(
      `${this.apiUrl}/attributes/${attributeId}`,
      { withCredentials: true }
    );
  }

  /**
   * Create a new attribute for a category.
   */
  createAttribute(
    categoryId: string,
    data: ICategoryAttributeCreate
  ): Observable<ICategoryAttribute> {
    return this.http.post<ICategoryAttribute>(
      `${this.apiUrl}/categories/${categoryId}/attributes`,
      { ...data, categoryId },
      { withCredentials: true }
    );
  }

  /**
   * Update an attribute.
   */
  updateAttribute(
    attributeId: string,
    data: ICategoryAttributeUpdate
  ): Observable<ICategoryAttribute> {
    return this.http.patch<ICategoryAttribute>(
      `${this.apiUrl}/attributes/${attributeId}`,
      data,
      { withCredentials: true }
    );
  }

  /**
   * Delete an attribute.
   */
  deleteAttribute(attributeId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/attributes/${attributeId}`, {
      withCredentials: true,
    });
  }

  /**
   * Get all global attributes (apply to all inventory items).
   */
  getGlobalAttributes(
    includeInactive = false
  ): Observable<ICategoryAttributeListResponse> {
    let params = new HttpParams();
    if (includeInactive) {
      params = params.set('include_inactive', 'true');
    }
    return this.http
      .get<ICategoryAttribute[]>(`${this.apiUrl}/attributes/global`, {
        params,
        withCredentials: true,
      })
      .pipe(map((items) => ({ items })));
  }

  /**
   * Create a new global attribute.
   */
  createGlobalAttribute(
    data: ICategoryAttributeCreate
  ): Observable<ICategoryAttribute> {
    return this.http.post<ICategoryAttribute>(
      `${this.apiUrl}/attributes/global`,
      { ...data, isGlobal: true },
      { withCredentials: true }
    );
  }

  /**
   * Reorder attributes within a category.
   */
  reorderAttributes(
    categoryId: string,
    attributeIds: string[]
  ): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.apiUrl}/categories/${categoryId}/attributes/reorder`,
      { attributeIds },
      { withCredentials: true }
    );
  }
}
