import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ICategory, ICategoryTreeNode } from '../models/category.model';
import { environment } from '../../../../environments/environment';
import {
  IDataResponse,
  IListResponse,
  IMessageResponse,
  IPaginationMeta
} from '../../../models/api-response.model';

export interface ICategoryListResult {
  items: ICategory[];
  pagination: IPaginationMeta;
}

@Injectable({
  providedIn: 'root'
})
export class CategoryService {
  private apiUrl = `${environment.apiUrl}/categories`;

  constructor(private http: HttpClient) { }

  getCategories(page: number = 1, pageSize: number = 25, isActive?: boolean, parentId?: string): Observable<ICategoryListResult> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('pageSize', pageSize.toString());

    if (isActive !== undefined) {
      params = params.set('isActive', isActive.toString());
    }
    if (parentId !== undefined) {
      params = params.set('parentId', parentId);
    }

    return this.http.get<IListResponse<ICategory>>(this.apiUrl, { params })
      .pipe(
        map(response => ({
          items: response.data,
          pagination: response.meta
        }))
      );
  }

  getCategoryTree(isActive?: boolean): Observable<ICategoryTreeNode[]> {
    let params = new HttpParams();
    if (isActive !== undefined) {
      params = params.set('isActive', isActive.toString());
    }

    return this.http.get<IDataResponse<ICategoryTreeNode[]>>(`${this.apiUrl}/tree`, { params })
      .pipe(map(response => response.data));
  }

  getCategory(id: string): Observable<ICategory> {
    return this.http.get<IDataResponse<ICategory>>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.data));
  }

  createCategory(category: ICategory): Observable<ICategory> {
    return this.http.post<IDataResponse<ICategory>>(this.apiUrl, category)
      .pipe(map(response => response.data));
  }

  updateCategory(id: string, category: Partial<ICategory>): Observable<ICategory> {
    return this.http.put<IDataResponse<ICategory>>(`${this.apiUrl}/${id}`, category)
      .pipe(map(response => response.data));
  }

  deleteCategory(id: string): Observable<string> {
    return this.http.delete<IMessageResponse>(`${this.apiUrl}/${id}`)
      .pipe(map(response => response.message));
  }
}
