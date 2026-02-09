import { z } from 'zod';
import type { RuleType } from '@/config/billingRuleConfig';

export const billingRuleFormSchema = z.object({
  project_id: z.string().uuid('Project is required'),
  rule_type: z.string().min(1, 'Rule type is required') as z.ZodType<RuleType>,
  rate_cents: z.coerce.number().min(0, 'Rate must be 0 or greater'),
  currency: z.string().length(3, 'Currency must be 3 letters').default('USD'),
  
  // Hourly rule fields
  rounding_increment_minutes: z.coerce.number().optional(),
  overtime_multiplier: z.coerce.number().optional(),
  cap_hours: z.coerce.number().optional(),
  
  // Retainer rule fields
  retainer_hours: z.coerce.number().optional(),
  
  // Session-based rule fields
  session_max_duration: z.coerce.number().optional(),
  
  // Per-item rule fields
  item_description: z.string().optional(),
  
  // Tiered rule fields
  tier1_threshold: z.coerce.number().optional(),
  tier1_rate_cents: z.coerce.number().optional(),
  tier2_threshold: z.coerce.number().optional(),
  tier2_rate_cents: z.coerce.number().optional(),
  tier3_rate_cents: z.coerce.number().optional(),
  
  // Event-based rule fields
  event_types: z.array(z.string()).optional(),
  rate_per_event_cents: z.coerce.number().optional(),
  
  // Travel fee fields
  hourly_rate_cents: z.coerce.number().optional(),
  mileage_rate_cents: z.coerce.number().optional(),
  parking_charges: z.boolean().optional(),
  
  // Date fields
  effective_from: z.string().optional(),
  effective_to: z.string().optional(),
  
  // Metadata
  meta: z.record(z.any()).optional(),
}).refine(
  (data) => {
    if (!data.effective_from || !data.effective_to) return true;
    return new Date(data.effective_from) < new Date(data.effective_to);
  },
  {
    message: 'Effective end date must be after start date',
    path: ['effective_to'],
  }
).refine(
  (data) => {
    if (data.rule_type === 'retainer') {
      return data.retainer_hours && data.retainer_hours > 0;
    }
    return true;
  },
  {
    message: 'Retainer rules must specify included hours',
    path: ['retainer_hours'],
  }
).refine(
  (data) => {
    if (data.rule_type === 'tiered') {
      return (
        (data.tier1_rate_cents ?? 0) >= 0 &&
        (data.tier2_rate_cents ?? 0) >= 0
      );
    }
    return true;
  },
  {
    message: 'Tiered pricing must have tier rates defined',
    path: ['tier1_rate_cents'],
  }
);

export type BillingRuleFormData = z.infer<typeof billingRuleFormSchema>;
