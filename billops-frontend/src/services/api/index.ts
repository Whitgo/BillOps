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

  // Time Capture
  timeCapture: {
    list: '/time-capture',
    get: (id: string) => `/time-capture/${id}`,
    create: '/time-capture',
    update: (id: string) => `/time-capture/${id}`,
    delete: (id: string) => `/time-capture/${id}`,
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
