/**
 * Authentication service functions
 */

import httpClient from '@/services/api/client';
import { AuthResponse, LoginCredentials, SignupData, ForgotPasswordData, ResetPasswordData } from '@/types/auth';

const AUTH_ENDPOINTS = {
  login: '/auth/login',
  signup: '/auth/signup',
  logout: '/auth/logout',
  refresh: '/auth/refresh',
  forgotPassword: '/auth/forgot-password',
  resetPassword: '/auth/reset-password',
  me: '/auth/me',
};

export const authService = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await httpClient.post<AuthResponse>(
      AUTH_ENDPOINTS.login,
      credentials
    );
    return response.data;
  },

  /**
   * Sign up with email and password
   */
  async signup(data: SignupData): Promise<AuthResponse> {
    const response = await httpClient.post<AuthResponse>(
      AUTH_ENDPOINTS.signup,
      {
        name: data.name,
        email: data.email,
        password: data.password,
      }
    );
    return response.data;
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    await httpClient.post(AUTH_ENDPOINTS.logout);
  },

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken(refreshToken: string): Promise<AuthResponse> {
    const response = await httpClient.post<AuthResponse>(
      AUTH_ENDPOINTS.refresh,
      { refreshToken }
    );
    return response.data;
  },

  /**
   * Request password reset
   */
  async forgotPassword(data: ForgotPasswordData): Promise<void> {
    await httpClient.post(AUTH_ENDPOINTS.forgotPassword, data);
  },

  /**
   * Reset password with token
   */
  async resetPassword(data: ResetPasswordData): Promise<void> {
    await httpClient.post(AUTH_ENDPOINTS.resetPassword, {
      token: data.token,
      password: data.password,
    });
  },

  /**
   * Get current user
   */
  async getCurrentUser() {
    const response = await httpClient.get(AUTH_ENDPOINTS.me);
    return response.data;
  },
};

export default authService;
