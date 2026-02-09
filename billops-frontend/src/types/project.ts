/**
 * Project type definitions
 */

export interface Project {
  id: string;
  name: string;
  client_id?: string;
  description?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProjectListResponse {
  items: Project[];
  total?: number;
}
