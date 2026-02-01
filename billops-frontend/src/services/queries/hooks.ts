/**
 * React Query hooks for common queries
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService, { apiEndpoints } from '@/services/api';

// Query keys for React Query cache management
export const queryKeys = {
  users: {
    all: ['users'] as const,
    list: () => [...queryKeys.users.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.users.all, 'detail', id] as const,
  },
  invoices: {
    all: ['invoices'] as const,
    list: () => [...queryKeys.invoices.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.invoices.all, 'detail', id] as const,
  },
  timeCapture: {
    all: ['time-capture'] as const,
    list: () => [...queryKeys.timeCapture.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.timeCapture.all, 'detail', id] as const,
  },
  notifications: {
    all: ['notifications'] as const,
    list: () => [...queryKeys.notifications.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.notifications.all, 'detail', id] as const,
  },
  reports: {
    all: ['reports'] as const,
    list: () => [...queryKeys.reports.all, 'list'] as const,
  },
};

// Default query options
export const defaultQueryOptions = {
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  retry: 1,
  refetchOnWindowFocus: false,
};

/**
 * Custom hook for fetching users
 */
export const useUsers = () => {
  return useQuery({
    queryKey: queryKeys.users.list(),
    queryFn: () => apiService.fetch(apiEndpoints.users.list),
    ...defaultQueryOptions,
  });
};

/**
 * Custom hook for fetching a single user
 */
export const useUser = (id: string) => {
  return useQuery({
    queryKey: queryKeys.users.detail(id),
    queryFn: () => apiService.fetch(apiEndpoints.users.get(id)),
    enabled: !!id,
    ...defaultQueryOptions,
  });
};

/**
 * Custom hook for creating a user
 */
export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: unknown) => apiService.create(apiEndpoints.users.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
};

/**
 * Custom hook for updating a user
 */
export const useUpdateUser = (id: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: unknown) => apiService.update(apiEndpoints.users.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.users.detail(id) });
    },
  });
};

/**
 * Custom hook for deleting a user
 */
export const useDeleteUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiService.delete(apiEndpoints.users.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
};

/**
 * Custom hook for fetching invoices
 */
export const useInvoices = () => {
  return useQuery({
    queryKey: queryKeys.invoices.list(),
    queryFn: () => apiService.fetch(apiEndpoints.invoices.list),
    ...defaultQueryOptions,
  });
};

/**
 * Custom hook for fetching a single invoice
 */
export const useInvoice = (id: string) => {
  return useQuery({
    queryKey: queryKeys.invoices.detail(id),
    queryFn: () => apiService.fetch(apiEndpoints.invoices.get(id)),
    enabled: !!id,
    ...defaultQueryOptions,
  });
};

/**
 * Custom hook for fetching time capture entries
 */
export const useTimeCapture = () => {
  return useQuery({
    queryKey: queryKeys.timeCapture.list(),
    queryFn: () => apiService.fetch(apiEndpoints.timeCapture.list),
    ...defaultQueryOptions,
  });
};

/**
 * Custom hook for fetching notifications
 */
export const useNotifications = () => {
  return useQuery({
    queryKey: queryKeys.notifications.list(),
    queryFn: () => apiService.fetch(apiEndpoints.notifications.list),
    ...defaultQueryOptions,
  });
};
