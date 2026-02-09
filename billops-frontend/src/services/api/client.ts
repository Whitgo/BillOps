/**
 * HTTP Client with error handling and interceptors
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import config from '@/config';
import { ApiError } from '@/types/api';

interface AuthAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

class HttpClient {
  private instance: AxiosInstance;
  private isRefreshing = false;
  private refreshPromise: Promise<string | null> | null = null;

  constructor() {
    this.instance = axios.create({
      baseURL: config.apiUrl,
      timeout: config.apiTimeout,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.instance.interceptors.request.use(
      (requestConfig: AuthAxiosRequestConfig) => {
        // Add auth token if available
        const token = localStorage.getItem('accessToken');
        if (token) {
          requestConfig.headers.Authorization = `Bearer ${token}`;
        }

        // Log request in debug mode
        if (config.enableDebug) {
          console.log('API Request:', requestConfig);
        }

        return requestConfig;
      },
      (error) => {
        return Promise.reject(this.handleError(error));
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        if (config.enableDebug) {
          console.log('API Response:', response);
        }
        return response;
      },
      async (error) => {
        if (axios.isAxiosError(error)) {
          const originalRequest = error.config as AuthAxiosRequestConfig | undefined;
          const status = error.response?.status;

          if (status === 401 && originalRequest && !originalRequest._retry) {
            originalRequest._retry = true;

            const newAccessToken = await this.refreshAccessToken();
            if (newAccessToken) {
              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
              return this.instance(originalRequest);
            }
          }
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  private async refreshAccessToken(): Promise<string | null> {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      this.clearAuthAndRedirect();
      return null;
    }

    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = axios
      .post<{ tokens: { accessToken: string; refreshToken: string } }>(
        `${config.apiUrl}/auth/refresh`,
        { refreshToken }
      )
      .then((response) => {
        const { accessToken, refreshToken: newRefreshToken } = response.data.tokens;
        localStorage.setItem('accessToken', accessToken);
        localStorage.setItem('refreshToken', newRefreshToken);
        return accessToken;
      })
      .catch(() => {
        this.clearAuthAndRedirect();
        return null;
      })
      .finally(() => {
        this.isRefreshing = false;
        this.refreshPromise = null;
      });

    return this.refreshPromise;
  }

  private clearAuthAndRedirect() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }

  private handleError(error: unknown): ApiError {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status || 500;
      const message =
        error.response?.data?.message ||
        error.message ||
        'An error occurred';
      const details = error.response?.data?.details || error.response?.data;

      // Handle specific status codes
      if (status === 401) {
        this.clearAuthAndRedirect();
      }

      if (status === 403) {
        // Forbidden
        console.error('Access denied');
      }

      if (config.enableDebug) {
        console.error('API Error:', { status, message, details });
      }

      return {
        status,
        message,
        details,
        originalError: error as Error,
      };
    }

    return {
      status: 500,
      message: 'An unexpected error occurred',
      originalError: error as Error,
    };
  }

  async get<T = unknown>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.get<T>(url, config);
  }

  async post<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.post<T>(url, data, config);
  }

  async put<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.put<T>(url, data, config);
  }

  async patch<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.patch<T>(url, data, config);
  }

  async delete<T = unknown>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.instance.delete<T>(url, config);
  }

  getInstance(): AxiosInstance {
    return this.instance;
  }
}

export default new HttpClient();
