/**
 * Billing Rule Templates for professions
 * Each template defines a rule type and default values to pre-populate the form.
 */

import type { RuleType } from '@/config/billingRuleConfig';
import type { BillingRuleFormData } from '@/schemas/billingRule';

export interface BillingRuleTemplate {
  id: string;
  label: string;
  description: string;
  ruleType: RuleType;
  defaults: Partial<BillingRuleFormData>;
}

export const BILLING_RULE_TEMPLATES: BillingRuleTemplate[] = [
  {
    id: 'coach',
    label: 'Coach',
    description: 'Session-based coaching with a standard 60 minute session rate.',
    ruleType: 'session-based',
    defaults: {
      rate_cents: 15000,
      currency: 'USD',
      session_max_duration: 60,
    },
  },
  {
    id: 'notary',
    label: 'Notary',
    description: 'Per-item fee per notarization.',
    ruleType: 'per-item',
    defaults: {
      rate_cents: 2500,
      currency: 'USD',
      item_description: 'Notarization',
    },
  },
  {
    id: 'artist',
    label: 'Artist',
    description: 'Fixed fee for commissioned work.',
    ruleType: 'fixed',
    defaults: {
      rate_cents: 200000,
      currency: 'USD',
    },
  },
  {
    id: 'designer',
    label: 'Designer',
    description: 'Hourly billing with rounding and overtime.',
    ruleType: 'hourly',
    defaults: {
      rate_cents: 8500,
      currency: 'USD',
      rounding_increment_minutes: 15,
      overtime_multiplier: 1.5,
      cap_hours: 160,
    },
  },
  {
    id: 'photographer',
    label: 'Photographer',
    description: 'Event-based pricing per shoot or session.',
    ruleType: 'event-based',
    defaults: {
      rate_cents: 30000,
      currency: 'USD',
      rate_per_event_cents: 30000,
      event_types: ['Shoot', 'Editing'],
    },
  },
  {
    id: 'tutor',
    label: 'Tutor',
    description: 'Session-based tutoring with a standard 60 minute session.',
    ruleType: 'session-based',
    defaults: {
      rate_cents: 7500,
      currency: 'USD',
      session_max_duration: 60,
    },
  },
  {
    id: 'consultant',
    label: 'Consultant',
    description: 'Monthly retainer with included hours and overage multiplier.',
    ruleType: 'retainer',
    defaults: {
      rate_cents: 500000,
      currency: 'USD',
      retainer_hours: 20,
      overtime_multiplier: 1.5,
    },
  },
];

export const getBillingRuleTemplateOptions = () =>
  BILLING_RULE_TEMPLATES.map((template) => ({
    label: template.label,
    value: template.id,
  }));

export const getBillingRuleTemplate = (templateId: string) =>
  BILLING_RULE_TEMPLATES.find((template) => template.id === templateId);
