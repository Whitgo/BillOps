/**
 * API Response types
 */

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string | null;
  message?: string;
  status: number;
}

export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, unknown>;
  originalError?: Error;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
