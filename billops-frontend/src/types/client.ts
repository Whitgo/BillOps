/**
 * Client type definitions
 */

export interface Client {
  id: string;
  name: string;
  currency?: string;
  contact_email?: string;
  contact_name?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ClientListResponse {
  items: Client[];
  total?: number;
}
