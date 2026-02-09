import type { RuleType } from '@/config/billingRuleConfig';

export interface BillingRule {
  id: string;
  project_id: string;
  rule_type: RuleType;
  rate_cents: number;
  currency: string;
  rounding_increment_minutes?: number;
  overtime_multiplier?: number;
  cap_hours?: number;
  retainer_hours?: number;
  effective_from: string;
  effective_to?: string;
  meta?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface BillingRuleListResponse {
  items: BillingRule[];
  total: number;
  skip: number;
  limit: number;
}

export interface BillingRuleFormData {
  project_id: string;
  rule_type: RuleType;
  rate_cents: number;
  currency: string;
  rounding_increment_minutes?: number;
  overtime_multiplier?: number;
  cap_hours?: number;
  retainer_hours?: number;
  session_max_duration?: number;
  item_description?: string;
  tier1_threshold?: number;
  tier1_rate_cents?: number;
  tier2_threshold?: number;
  tier2_rate_cents?: number;
  tier3_rate_cents?: number;
  event_types?: string[];
  rate_per_event_cents?: number;
  hourly_rate_cents?: number;
  mileage_rate_cents?: number;
  parking_charges?: boolean;
  meta?: Record<string, unknown>;
  effective_from: string;
  effective_to?: string;
}
