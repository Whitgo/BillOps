/**
 * React Query hooks for common queries
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService, { apiEndpoints } from '@/services/api';
import type { Client, ClientListResponse } from '@/types/client';
import type { Project, ProjectListResponse } from '@/types/project';
import type {
  ActivitySignal,
  TimeEntry,
  TimeEntryListResponse,
  IngestTaskStatus,
} from '@/types/timeEntry';
import type { TimeEntryFormData, TimeEntryUpdateData } from '@/schemas/timeEntry';
import type { BillingRule, BillingRuleListResponse } from '@/types/billingRule';
import type { BillingRuleFormData } from '@/schemas/billingRule';

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
  clients: {
    all: ['clients'] as const,
    list: (skip: number, limit: number) =>
      [...queryKeys.clients.all, 'list', skip, limit] as const,
  },
  projects: {
    all: ['projects'] as const,
    list: (skip: number, limit: number, clientId?: string) =>
      [...queryKeys.projects.all, 'list', skip, limit, clientId || 'all'] as const,
  },
  timeEntries: {
    all: ['time-entries'] as const,
    list: (skip: number, limit: number) =>
      [...queryKeys.timeEntries.all, 'list', skip, limit] as const,
    pendingReview: (skip: number, limit: number) =>
      [...queryKeys.timeEntries.all, 'pending-review', skip, limit] as const,
    detail: (id: string) => [...queryKeys.timeEntries.all, 'detail', id] as const,
    ingestStatus: (taskId: string) =>
      [...queryKeys.timeEntries.all, 'ingest-status', taskId] as const,
  },
  billingRules: {
    all: ['billing-rules'] as const,
    list: (skip: number, limit: number, projectId?: string) =>
      [...queryKeys.billingRules.all, 'list', skip, limit, projectId || 'all'] as const,
    detail: (id: string) => [...queryKeys.billingRules.all, 'detail', id] as const,
  },
};

// Default query options
export const defaultQueryOptions = {
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  retry: 1,
  refetchOnWindowFocus: false,
};

const updateListCache = <T>(
  oldData: unknown,
  updater: (items: T[]) => T[]
): unknown => {
  if (Array.isArray(oldData)) {
    return updater(oldData as T[]);
  }
  if (oldData && typeof oldData === 'object' && 'items' in (oldData as Record<string, unknown>)) {
    const data = oldData as { items: T[]; total?: number };
    return {
      ...data,
      items: updater(data.items || []),
      total: data.total,
    };
  }
  return oldData;
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
    queryKey: queryKeys.timeEntries.list(0, 10),
    queryFn: async () => {
      const response = await apiService.fetch<TimeEntryListResponse>(apiEndpoints.timeEntries.list);
      return response.data as TimeEntryListResponse;
    },
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

/**
 * Clients
 */
export const useClients = (skip: number, limit: number) => {
  const url = `${apiEndpoints.clients.list}?skip=${skip}&limit=${limit}`;
  return useQuery<ClientListResponse>({
    queryKey: queryKeys.clients.list(skip, limit),
    queryFn: async () => {
      const response = await apiService.fetch<ClientListResponse>(url);
      return response.data as ClientListResponse;
    },
    ...defaultQueryOptions,
  });
};

export const useCreateClient = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Client>) => apiService.create(apiEndpoints.clients.create, data),
    onMutate: async (newClient) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.clients.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.clients.all });

      const optimisticClient: Client = {
        id: `temp-${Date.now()}`,
        name: newClient.name || 'New Client',
        currency: newClient.currency,
        contact_email: newClient.contact_email,
        contact_name: newClient.contact_name,
        is_active: true,
      };

      previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, updateListCache<Client>(data, (items) => [optimisticClient, ...items]));
      });

      return { previous };
    },
    onError: (_err, _newClient, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.clients.all });
    },
  });
};

export const useUpdateClient = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Client> }) =>
      apiService.patch(apiEndpoints.clients.update(id), data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.clients.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.clients.all });

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<Client>(oldData, (items) =>
          items.map((item) => (item.id === id ? { ...item, ...data } : item))
        ));
      });

      return { previous };
    },
    onError: (_err, _variables, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.clients.all });
    },
  });
};

export const useDeleteClient = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiService.delete(apiEndpoints.clients.delete(id)),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.clients.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.clients.all });

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<Client>(oldData, (items) =>
          items.filter((item) => item.id !== id)
        ));
      });

      return { previous };
    },
    onError: (_err, _id, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.clients.all });
    },
  });
};

/**
 * Projects
 */
export const useProjects = (skip: number, limit: number, clientId?: string) => {
  const query = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
    ...(clientId ? { client_id: clientId } : {}),
  });
  const url = `${apiEndpoints.projects.list}?${query.toString()}`;
  return useQuery<ProjectListResponse>({
    queryKey: queryKeys.projects.list(skip, limit, clientId),
    queryFn: async () => {
      const response = await apiService.fetch<ProjectListResponse>(url);
      return response.data as ProjectListResponse;
    },
    ...defaultQueryOptions,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Project>) => apiService.create(apiEndpoints.projects.create, data),
    onMutate: async (newProject) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.projects.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.projects.all });

      const optimisticProject: Project = {
        id: `temp-${Date.now()}`,
        name: newProject.name || 'New Project',
        client_id: newProject.client_id,
        description: newProject.description,
        is_active: true,
      };

      previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, updateListCache<Project>(data, (items) => [optimisticProject, ...items]));
      });

      return { previous };
    },
    onError: (_err, _newProject, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
};

export const useUpdateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) =>
      apiService.patch(apiEndpoints.projects.update(id), data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.projects.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.projects.all });

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<Project>(oldData, (items) =>
          items.map((item) => (item.id === id ? { ...item, ...data } : item))
        ));
      });

      return { previous };
    },
    onError: (_err, _variables, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiService.delete(apiEndpoints.projects.delete(id)),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.projects.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.projects.all });

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<Project>(oldData, (items) =>
          items.filter((item) => item.id !== id)
        ));
      });

      return { previous };
    },
    onError: (_err, _id, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
};

// Time Entry Hooks

export const usePendingTimeEntries = (skip: number, limit: number) => {
  return useQuery<TimeEntryListResponse>({
    queryKey: queryKeys.timeEntries.pendingReview(skip, limit),
    queryFn: async () => {
      const url = `${apiEndpoints.timeEntries.pendingReview}?skip=${skip}&limit=${limit}`;
      const response = await apiService.fetch<TimeEntryListResponse>(url);
      return response.data as TimeEntryListResponse;
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Poll every 30 seconds
  });
};

export const useApproveTimeEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { id: string; entry: TimeEntryUpdateData }) =>
      apiService.patch<TimeEntry>(
        apiEndpoints.timeEntries.update(data.id),
        { ...data.entry, status: 'approved' }
      ),
    onMutate: async ({ id, entry }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.timeEntries.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.timeEntries.all });

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<TimeEntry>(oldData, (items) =>
          items.map((item) =>
            item.id === id
              ? {
                  ...item,
                  status: 'approved',
                  project_id: entry.project_id || item.project_id,
                  client_id: entry.client_id || item.client_id,
                  activity_type: entry.activity_type || item.activity_type,
                  notes: entry.notes || item.notes,
                }
              : item
          )
        ));
      });

      return { previous };
    },
    onError: (_err, _variables, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.timeEntries.all });
    },
  });
};

export const useRejectTimeEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { id: string; entry: TimeEntryUpdateData }) =>
      apiService.patch<TimeEntry>(
        apiEndpoints.timeEntries.update(data.id),
        { ...data.entry, status: 'rejected' }
      ),
    onMutate: async ({ id }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.timeEntries.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.timeEntries.all });

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<TimeEntry>(oldData, (items) =>
          items.filter((item) => item.id !== id)
        ));
      });

      return { previous };
    },
    onError: (_err, _variables, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.timeEntries.all });
    },
  });
};

export const useCreateTimeEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TimeEntryFormData) =>
      apiService.create<TimeEntry>(apiEndpoints.timeEntries.create, data),
    onMutate: async (newEntry) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.timeEntries.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.timeEntries.all });

      // Create optimistic time entry
      const optimisticEntry: TimeEntry = {
        id: `temp-${Date.now()}`,
        started_at: newEntry.started_at,
        ended_at: newEntry.ended_at,
        duration_minutes: Math.round(
          (new Date(newEntry.ended_at).getTime() - new Date(newEntry.started_at).getTime()) / 60000
        ),
        status: 'approved',
        source: 'manual',
        project_id: newEntry.project_id,
        client_id: newEntry.client_id,
        activity_type: newEntry.activity_type,
        notes: newEntry.notes,
      };

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<TimeEntry>(oldData, (items) => [
          optimisticEntry,
          ...items,
        ]));
      });

      return { previous };
    },
    onError: (_err, _newEntry, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.timeEntries.all });
    },
  });
};

export const useIngestActivitySignals = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (signals: ActivitySignal[]) =>
      apiService.create<{ task_id: string }>(
        apiEndpoints.timeEntries.ingest,
        { activity_signals: signals }
      ),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.timeEntries.all });
    },
  });
};

export const useIngestTaskStatus = (taskId: string | null) => {
  return useQuery<IngestTaskStatus>({
    queryKey: queryKeys.timeEntries.ingestStatus(taskId || ''),
    queryFn: async () => {
      const response = await apiService.fetch<IngestTaskStatus>(
        apiEndpoints.timeEntries.ingestStatus(taskId!)
      );
      return response.data as IngestTaskStatus;
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      // Stop polling once task is complete
      const data = query.state.data as IngestTaskStatus | undefined;
      if (data?.status === 'SUCCESS' || data?.status === 'FAILURE') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });
};

// Billing Rules Hooks

export const useBillingRules = (skip: number, limit: number, projectId?: string) => {
  const query = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
    ...(projectId ? { project_id: projectId } : {}),
  });
  const url = `${apiEndpoints.billingRules.list}?${query.toString()}`;
  return useQuery<BillingRuleListResponse>({
    queryKey: queryKeys.billingRules.list(skip, limit, projectId),
    queryFn: async () => {
      const response = await apiService.fetch<BillingRuleListResponse>(url);
      return response.data as BillingRuleListResponse;
    },
    ...defaultQueryOptions,
  });
};

export const useCreateBillingRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BillingRuleFormData) =>
      apiService.create<BillingRule>(apiEndpoints.billingRules.create, data),
    onMutate: async (newRule) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.billingRules.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.billingRules.all });

      const optimisticRule: BillingRule = {
        id: `temp-${Date.now()}`,
        project_id: newRule.project_id,
        rule_type: newRule.rule_type,
        rate_cents: newRule.rate_cents,
        currency: newRule.currency,
        rounding_increment_minutes: newRule.rounding_increment_minutes,
        overtime_multiplier: newRule.overtime_multiplier,
        cap_hours: newRule.cap_hours,
        retainer_hours: newRule.retainer_hours,
        effective_from: newRule.effective_from || new Date().toISOString(),
        effective_to: newRule.effective_to || undefined,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<BillingRule>(oldData, (items) =>
          [optimisticRule, ...items]
        ));
      });

      return { previous };
    },
    onError: (_err, _newRule, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.billingRules.all });
    },
  });
};

export const useUpdateBillingRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<BillingRuleFormData> }) =>
      apiService.patch<BillingRule>(apiEndpoints.billingRules.update(id), data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.billingRules.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.billingRules.all });

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<BillingRule>(oldData, (items) =>
          items.map((item) => (item.id === id ? { ...item, ...data } : item))
        ));
      });

      return { previous };
    },
    onError: (_err, _variables, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.billingRules.all });
    },
  });
};

export const useDeleteBillingRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiService.delete(apiEndpoints.billingRules.delete(id)),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.billingRules.all });
      const previous = queryClient.getQueriesData({ queryKey: queryKeys.billingRules.all });

      previous.forEach(([key, oldData]) => {
        queryClient.setQueryData(key, updateListCache<BillingRule>(oldData, (items) =>
          items.filter((item) => item.id !== id)
        ));
      });

      return { previous };
    },
    onError: (_err, _id, context) => {
      context?.previous.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.billingRules.all });
    },
  });
};

