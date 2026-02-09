/* eslint-disable react-refresh/only-export-components */
/**
 * Authentication Context and Provider
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { ReactNode } from 'react';
import authService from '@/services/auth';
import {
  AuthContextType,
  User,
  LoginCredentials,
  SignupData,
  ForgotPasswordData,
  ResetPasswordData,
} from '@/types/auth';

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'accessToken',
  REFRESH_TOKEN: 'refreshToken',
  USER: 'user',
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Clear all auth data
   */
  const clearAuth = useCallback(() => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }, []);

  /**
   * Initialize auth state from localStorage
   */
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
        const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);

        if (storedUser && accessToken) {
          setUser(JSON.parse(storedUser));
        }
      } catch (err) {
        console.error('Failed to initialize auth:', err);
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [clearAuth]);

  /**
   * Login
   */
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authService.login(credentials);
      
      // Store tokens
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.tokens.accessToken);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.tokens.refreshToken);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.user));

      setUser(response.user);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Sign up
   */
  const signup = useCallback(async (data: SignupData) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authService.signup(data);

      // Store tokens
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.tokens.accessToken);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.tokens.refreshToken);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.user));

      setUser(response.user);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Signup failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Logout
   */
  const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      clearAuth();
      setIsLoading(false);
    }
  }, [clearAuth]);

  /**
   * Forgot password
   */
  const forgotPassword = useCallback(async (data: ForgotPasswordData) => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.forgotPassword(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Request failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Reset password
   */
  const resetPassword = useCallback(async (data: ResetPasswordData) => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.resetPassword(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Reset failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Refresh access token
   */
  const refreshAccessToken = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
      if (!refreshToken) {
        clearAuth();
        return;
      }

      const response = await authService.refreshAccessToken(refreshToken);
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.tokens.accessToken);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.tokens.refreshToken);

      if (response.user) {
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.user));
        setUser(response.user);
      }
    } catch (err) {
      console.error('Token refresh failed:', err);
      clearAuth();
      throw err;
    }
  }, [clearAuth]);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    signup,
    logout,
    forgotPassword,
    resetPassword,
    refreshAccessToken,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to use auth context
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
