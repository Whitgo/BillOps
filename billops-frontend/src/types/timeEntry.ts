export interface TimeEntry {
  id: string;
  started_at: string;
  ended_at: string;
  duration_minutes: number;
  status: 'pending' | 'approved' | 'rejected';
  source: 'auto' | 'manual';
  project_id?: string;
  client_id?: string;
  activity_type?: string;
  notes?: string;
  context_data?: {
    confidence?: number;
    applications?: string[];
    primary_activity?: string;
  };
}

export interface TimeEntryListResponse {
  total: number;
  skip: number;
  limit: number;
  entries: TimeEntry[];
}

export interface IngestTaskStatus {
  task_id: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILURE' | 'RETRY';
  result?: {
    status: string;
    suggested_count: number;
    created_count: number;
    created_ids: string[];
    verification_required: Array<{
      confidence: number;
      reason: string;
      description: string;
    }>;
  };
  error?: string;
}

export interface ActivitySignal {
  timestamp: string;
  app: string;
  type: string;
  source_type: string;
}

export interface TimeEntryFormData {
  started_at: string;
  ended_at: string;
  project_id?: string;
  client_id?: string;
  activity_type?: string;
  notes?: string;
}

export interface TimeEntryUpdate {
  status: 'approved' | 'rejected';
  project_id?: string;
  client_id?: string;
  activity_type?: string;
  notes?: string;
}
