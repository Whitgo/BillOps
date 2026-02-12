import { z } from 'zod';
import type { RuleType } from '@/config/billingRuleConfig';
import { billingRuleFormSchema } from './billingRule';

/**
 * Schema for a single billing rule block
 */
export const billingRuleBlockSchema = billingRuleFormSchema.extend({
  block_id: z.string().optional(), // Client-side ID for managing blocks
  enabled: z.boolean().default(true), // Enable/disable the block
  order: z.number().default(0), // Ordering within compound rule
});

export type BillingRuleBlock = z.infer<typeof billingRuleBlockSchema>;

/**
 * Schema for compound billing rules (multiple blocks)
 */
export const compoundBillingRuleSchema = z.object({
  project_id: z.string().uuid('Project is required'),
  blocks: z.array(billingRuleBlockSchema).min(1, 'At least one billing rule block is required'),
  effective_from: z.string().optional(),
  effective_to: z.string().optional(),
  name: z.string().optional(), // Optional name for the compound rule
});

export type CompoundBillingRuleFormData = z.infer<typeof compoundBillingRuleSchema>;

/**
 * API response for compound billing rules
 */
export interface CompoundBillingRule {
  id: string;
  project_id: string;
  blocks: BillingRuleBlock[];
  effective_from?: string;
  effective_to?: string;
  name?: string;
  created_at: string;
  updated_at: string;
}
