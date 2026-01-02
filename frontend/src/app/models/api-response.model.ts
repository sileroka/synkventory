/**
 * Standard API response metadata
 */
export interface IResponseMeta {
  timestamp: string;
  requestId: string;
}

/**
 * Pagination metadata for list responses
 */
export interface IPaginationMeta extends IResponseMeta {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

/**
 * Standard data response wrapper for single items
 */
export interface IDataResponse<T> {
  data: T;
  meta: IResponseMeta;
}

/**
 * Standard list response wrapper with pagination
 */
export interface IListResponse<T> {
  data: T[];
  meta: IPaginationMeta;
}

/**
 * Error detail structure
 */
export interface IErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Standard error response format
 */
export interface IErrorResponse {
  error: IErrorDetail;
  meta: IResponseMeta;
}

/**
 * Message response format
 */
export interface IMessageResponse {
  message: string;
  meta: IResponseMeta;
}
