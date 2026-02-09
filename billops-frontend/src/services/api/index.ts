/**
 * API endpoints and service methods
 */

import httpClient from './client';
import { ApiResponse } from '@/types/api';

export const apiEndpoints = {
  // Auth
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    me: '/auth/me',
  },

  // Users
  users: {
    list: '/users',
    get: (id: string) => `/users/${id}`,
    create: '/users',
    update: (id: string) => `/users/${id}`,
    delete: (id: string) => `/users/${id}`,
  },

  // Invoices
  invoices: {
    list: '/invoices',
    get: (id: string) => `/invoices/${id}`,
    create: '/invoices',
    update: (id: string) => `/invoices/${id}`,
    delete: (id: string) => `/invoices/${id}`,
  },

  // Billing Rules
  billingRules: {
    list: '/api/v1/billing-rules/',
    get: (id: string) => `/api/v1/billing-rules/${id}`,
    create: '/api/v1/billing-rules/',
    update: (id: string) => `/api/v1/billing-rules/${id}`,
    delete: (id: string) => `/api/v1/billing-rules/${id}`,
  },

  // Time Entries
  timeEntries: {
    list: '/api/v1/time-entries/',
    get: (id: string) => `/api/v1/time-entries/${id}`,
    create: '/api/v1/time-entries/',
    update: (id: string) => `/api/v1/time-entries/${id}`,
    delete: (id: string) => `/api/v1/time-entries/${id}`,
    pendingReview: '/api/v1/time-entries/pending-review',
    ingest: '/api/v1/time-entries/ingest',
    ingestStatus: (taskId: string) => `/api/v1/time-entries/ingest/${taskId}`,
  },

  // Notifications
  notifications: {
    list: '/notifications',
    get: (id: string) => `/notifications/${id}`,
    markAsRead: (id: string) => `/notifications/${id}/read`,
    markAllAsRead: '/notifications/read-all',
  },

  // Reports
  reports: {
    list: '/reports',
    generate: '/reports/generate',
  },

  // Clients
  clients: {
    list: '/api/v1/clients/',
    get: (id: string) => `/api/v1/clients/${id}`,
    create: '/api/v1/clients/',
    update: (id: string) => `/api/v1/clients/${id}`,
    delete: (id: string) => `/api/v1/clients/${id}`,
  },

  // Projects
  projects: {
    list: '/api/v1/projects/',
    get: (id: string) => `/api/v1/projects/${id}`,
    create: '/api/v1/projects/',
    update: (id: string) => `/api/v1/projects/${id}`,
    delete: (id: string) => `/api/v1/projects/${id}`,
  },
};

/**
 * Generic API service methods
 */
export const apiService = {
  /**
   * Fetch data with error handling
   */
  async fetch<T>(url: string) {
    const response = await httpClient.get<T>(url);
    return {
      success: true,
      data: response.data,
      status: response.status,
    } as ApiResponse<T>;
  },

  /**
   * Create new resource
   */
  async create<T>(url: string, payload: unknown) {
    const response = await httpClient.post<T>(url, payload);
    return {
      success: true,
      data: response.data,
      status: response.status,
    } as ApiResponse<T>;
  },

  /**
   * Update existing resource
   */
  async update<T>(url: string, payload: unknown) {
    const response = await httpClient.put<T>(url, payload);
    return {
      success: true,
      data: response.data,
      status: response.status,
    } as ApiResponse<T>;
  },

  /**
   * Partially update resource
   */
  async patch<T>(url: string, payload: unknown) {
    const response = await httpClient.patch<T>(url, payload);
    return {
      success: true,
      data: response.data,
      status: response.status,
    } as ApiResponse<T>;
  },

  /**
   * Delete resource
   */
  async delete(url: string) {
    await httpClient.delete(url);
    return {
      success: true,
      status: 204,
    } as ApiResponse<null>;
  },
};

export default apiService;
