import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  IUser,
  IUserCreate,
  IUserUpdate,
  IUserListResponse,
  IUserFilters,
  IPasswordChange,
  IPasswordReset
} from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/users`;

  /**
   * Get list of users with optional filtering and pagination.
   */
  getUsers(filters?: IUserFilters): Observable<IUserListResponse> {
    let params = new HttpParams();

    if (filters) {
      if (filters.page) {
        params = params.set('page', filters.page.toString());
      }
      if (filters.pageSize) {
        params = params.set('page_size', filters.pageSize.toString());
      }
      if (filters.search) {
        params = params.set('search', filters.search);
      }
      if (filters.isActive !== undefined) {
        params = params.set('is_active', filters.isActive.toString());
      }
      if (filters.role) {
        params = params.set('role', filters.role);
      }
    }

    return this.http.get<IUserListResponse>(this.apiUrl, { params });
  }

  /**
   * Get a single user by ID.
   */
  getUser(id: string): Observable<IUser> {
    return this.http.get<IUser>(`${this.apiUrl}/${id}`);
  }

  /**
   * Get the current user's information.
   */
  getCurrentUser(): Observable<IUser> {
    return this.http.get<IUser>(`${this.apiUrl}/me`);
  }

  /**
   * Create a new user.
   */
  createUser(user: IUserCreate): Observable<IUser> {
    return this.http.post<IUser>(this.apiUrl, user);
  }

  /**
   * Update a user.
   */
  updateUser(id: string, update: IUserUpdate): Observable<IUser> {
    return this.http.put<IUser>(`${this.apiUrl}/${id}`, update);
  }

  /**
   * Activate a user.
   */
  activateUser(id: string): Observable<IUser> {
    return this.http.post<IUser>(`${this.apiUrl}/${id}/activate`, {});
  }

  /**
   * Deactivate a user.
   */
  deactivateUser(id: string): Observable<IUser> {
    return this.http.post<IUser>(`${this.apiUrl}/${id}/deactivate`, {});
  }

  /**
   * Change the current user's password.
   */
  changePassword(passwordData: IPasswordChange): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(`${this.apiUrl}/me/password`, passwordData);
  }

  /**
   * Reset a user's password (admin/manager action).
   */
  resetUserPassword(id: string, passwordData: IPasswordReset): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/${id}/reset-password`, passwordData);
  }
}
