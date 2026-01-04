import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { IDataResponse } from '../models/api-response.model';

export interface IImageUploadResponse {
  imageKey: string;
  imageUrl: string;
}

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private readonly apiUrl = `${environment.apiUrl}/uploads`;

  constructor(private http: HttpClient) {}

  /**
   * Upload an image for an inventory item
   */
  uploadInventoryImage(itemId: string, file: File): Observable<IImageUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<IDataResponse<IImageUploadResponse>>(
      `${this.apiUrl}/inventory/${itemId}/image`,
      formData
    ).pipe(map(response => response.data));
  }

  /**
   * Delete an inventory item's image
   */
  deleteInventoryImage(itemId: string): Observable<void> {
    return this.http.delete<IDataResponse<{ message: string }>>(
      `${this.apiUrl}/inventory/${itemId}/image`
    ).pipe(map(() => undefined));
  }

  /**
   * Get a fresh signed URL for an inventory item's image
   */
  getInventoryImageUrl(itemId: string): Observable<string> {
    return this.http.get<IDataResponse<{ imageUrl: string }>>(
      `${this.apiUrl}/inventory/${itemId}/image-url`
    ).pipe(map(response => response.data.imageUrl));
  }
}
