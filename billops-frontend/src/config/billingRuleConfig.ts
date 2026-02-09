/**
 * Billing Rule Configuration
 * Defines rule types and their associated fields in a configuration-driven manner
 */

export type RuleType = 
  | 'hourly'
  | 'fixed'
  | 'retainer'
  | 'session-based'
  | 'per-item'
  | 'tiered'
  | 'event-based'
  | 'travel';

export interface RuleFieldConfig {
  name: string;
  label: string;
  type: 'number' | 'text' | 'date' | 'checkbox' | 'array';
  required?: boolean;
  description?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
  help?: string;
}

export interface RuleTypeConfig {
  type: RuleType;
  label: string;
  description: string;
  badge: {
    color: 'blue' | 'purple' | 'green' | 'orange' | 'red' | 'indigo' | 'pink' | 'gray';
    text: string;
  };
  baseFields: RuleFieldConfig[];
  conditionalFields?: Record<string, RuleFieldConfig[]>;
  previewTemplate: (data: RulePreviewData) => string;
}

export interface RulePreviewData {
  rate_cents?: number;
  currency?: string;
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
}

export const BILLING_RULE_TYPES: Record<RuleType, RuleTypeConfig> = {
  hourly: {
    type: 'hourly',
    label: 'Hourly Rate',
    description: 'Charges based on hours worked',
    badge: {
      color: 'blue',
      text: 'Hourly',
    },
    baseFields: [
      {
        name: 'rate_cents',
        label: 'Hourly Rate (cents)',
        type: 'number',
        required: true,
        placeholder: '15000',
        help: '150 dollars = 15000 cents',
        min: 0,
      },
      {
        name: 'currency',
        label: 'Currency',
        type: 'text',
        required: true,
        placeholder: 'USD',
        help: '3-letter ISO currency code',
      },
      {
        name: 'rounding_increment_minutes',
        label: 'Rounding Increment (minutes)',
        type: 'number',
        description: 'Round billable minutes to nearest increment',
        placeholder: '0',
        help: 'E.g., 15 = round to nearest 15 minutes',
        min: 0,
      },
      {
        name: 'overtime_multiplier',
        label: 'Overtime Multiplier',
        type: 'number',
        description: 'Multiplier for overtime hours (e.g., 1.5 for time-and-a-half)',
        placeholder: '1.5',
        min: 1,
        step: 0.1,
      },
      {
        name: 'cap_hours',
        label: 'Cap Hours per Period',
        type: 'number',
        description: 'Maximum billable hours per month (optional)',
        placeholder: '160',
        min: 0,
        step: 0.5,
      },
    ],
    previewTemplate: (data) => {
      const rate = data.rate_cents ? `$${(data.rate_cents / 100).toFixed(2)}/hr` : '$0/hr';
      const overtime = data.overtime_multiplier ? ` (${data.overtime_multiplier}x OT)` : '';
      const cap = data.cap_hours ? ` - ${data.cap_hours}h cap` : '';
      return `${rate}${overtime}${cap}`;
    },
  },

  fixed: {
    type: 'fixed',
    label: 'Fixed Fee',
    description: 'Flat fee regardless of hours',
    badge: {
      color: 'purple',
      text: 'Fixed',
    },
    baseFields: [
      {
        name: 'rate_cents',
        label: 'Fee Amount (cents)',
        type: 'number',
        required: true,
        placeholder: '50000',
        help: '500 dollars = 50000 cents',
        min: 0,
      },
      {
        name: 'currency',
        label: 'Currency',
        type: 'text',
        required: true,
        placeholder: 'USD',
        help: '3-letter ISO currency code',
      },
    ],
    previewTemplate: (data) => {
      const amount = data.rate_cents ? `$${(data.rate_cents / 100).toFixed(2)}` : '$0';
      return `${amount} flat fee`;
    },
  },

  retainer: {
    type: 'retainer',
    label: 'Retainer',
    description: 'Monthly retainer with included hours',
    badge: {
      color: 'green',
      text: 'Retainer',
    },
    baseFields: [
      {
        name: 'rate_cents',
        label: 'Monthly Retainer (cents)',
        type: 'number',
        required: true,
        placeholder: '300000',
        help: '3000 dollars = 300000 cents',
        min: 0,
      },
      {
        name: 'currency',
        label: 'Currency',
        type: 'text',
        required: true,
        placeholder: 'USD',
        help: '3-letter ISO currency code',
      },
      {
        name: 'retainer_hours',
        label: 'Included Hours',
        type: 'number',
        required: true,
        placeholder: '160',
        help: 'Hours included in retainer',
        min: 1,
        step: 0.5,
      },
      {
        name: 'overtime_multiplier',
        label: 'Overage Rate Multiplier',
        type: 'number',
        description: 'Multiplier for hours beyond retainer',
        placeholder: '1.5',
        min: 1,
        step: 0.1,
      },
    ],
    previewTemplate: (data) => {
      const amount = data.rate_cents ? `$${(data.rate_cents / 100).toFixed(2)}` : '$0';
      const hours = data.retainer_hours ? `/${data.retainer_hours}h` : '';
      const overage = data.overtime_multiplier ? ` + ${data.overtime_multiplier}x overage` : '';
      return `${amount}${hours}${overage}`;
    },
  },

  'session-based': {
    type: 'session-based',
    label: 'Session-Based',
    description: 'Hourly rate per session/meeting',
    badge: {
      color: 'orange',
      text: 'Session',
    },
    baseFields: [
      {
        name: 'rate_cents',
        label: 'Rate per Session (cents)',
        type: 'number',
        required: true,
        placeholder: '10000',
        help: '100 dollars per session = 10000 cents',
        min: 0,
      },
      {
        name: 'currency',
        label: 'Currency',
        type: 'text',
        required: true,
        placeholder: 'USD',
        help: '3-letter ISO currency code',
      },
      {
        name: 'session_max_duration',
        label: 'Max Session Duration (minutes)',
        type: 'number',
        description: 'Maximum duration per session before additional charges',
        placeholder: '60',
        min: 15,
        help: 'Sessions exceeding this duration incur additional charges',
      },
    ],
    previewTemplate: (data) => {
      const rate = data.rate_cents ? `$${(data.rate_cents / 100).toFixed(2)}` : '$0';
      const duration = data.session_max_duration ? ` (${data.session_max_duration}min max)` : '';
      return `${rate} per session${duration}`;
    },
  },

  'per-item': {
    type: 'per-item',
    label: 'Per Item',
    description: 'Fixed price per item/deliverable',
    badge: {
      color: 'indigo',
      text: 'Per Item',
    },
    baseFields: [
      {
        name: 'rate_cents',
        label: 'Price per Item (cents)',
        type: 'number',
        required: true,
        placeholder: '20000',
        help: '200 dollars per item = 20000 cents',
        min: 0,
      },
      {
        name: 'currency',
        label: 'Currency',
        type: 'text',
        required: true,
        placeholder: 'USD',
        help: '3-letter ISO currency code',
      },
      {
        name: 'item_description',
        label: 'Item Description',
        type: 'text',
        description: 'What is being billed (e.g., "Banner design", "Logo revision")',
        placeholder: 'Banner design',
      },
    ],
    previewTemplate: (data) => {
      const rate = data.rate_cents ? `$${(data.rate_cents / 100).toFixed(2)}` : '$0';
      const item = data.item_description ? ` per ${data.item_description}` : ' per item';
      return `${rate}${item}`;
    },
  },

  tiered: {
    type: 'tiered',
    label: 'Tiered Pricing',
    description: 'Variable rates based on volume/hours',
    badge: {
      color: 'pink',
      text: 'Tiered',
    },
    baseFields: [
      {
        name: 'currency',
        label: 'Currency',
        type: 'text',
        required: true,
        placeholder: 'USD',
        help: '3-letter ISO currency code',
      },
      {
        name: 'tier1_threshold',
        label: 'Tier 1 Hours Threshold',
        type: 'number',
        description: 'Hours before moving to next tier',
        placeholder: '100',
        help: 'First tier covers hours 0-100',
        min: 1,
      },
      {
        name: 'tier1_rate_cents',
        label: 'Tier 1 Rate (cents)',
        type: 'number',
        placeholder: '20000',
        help: '$200/hour for first 100 hours',
        min: 0,
      },
      {
        name: 'tier2_threshold',
        label: 'Tier 2 Hours Threshold',
        type: 'number',
        placeholder: '200',
        help: 'Hours 100-200 at tier 2 rate',
        min: 1,
      },
      {
        name: 'tier2_rate_cents',
        label: 'Tier 2 Rate (cents)',
        type: 'number',
        placeholder: '15000',
        help: '$150/hour for hours 100-200',
        min: 0,
      },
      {
        name: 'tier3_rate_cents',
        label: 'Tier 3 Rate (cents)',
        type: 'number',
        description: 'Rate for hours above Tier 2 threshold',
        placeholder: '10000',
        help: '$100/hour for 200+ hours',
        min: 0,
      },
    ],
    previewTemplate: (data) => {
      const t1 = data.tier1_rate_cents ? `$${(data.tier1_rate_cents / 100).toFixed(2)}` : '$0';
      const t2 = data.tier2_rate_cents ? `$${(data.tier2_rate_cents / 100).toFixed(2)}` : '$0';
      const t3 = data.tier3_rate_cents ? `$${(data.tier3_rate_cents / 100).toFixed(2)}` : '$0';
      return `${t1}→${t2}→${t3} tiered`;
    },
  },

  'event-based': {
    type: 'event-based',
    label: 'Event-Based',
    description: 'Charges based on specific events',
    badge: {
      color: 'red',
      text: 'Event',
    },
    baseFields: [
      {
        name: 'currency',
        label: 'Currency',
        type: 'text',
        required: true,
        placeholder: 'USD',
        help: '3-letter ISO currency code',
      },
      {
        name: 'event_types',
        label: 'Event Types',
        type: 'array',
        description: 'Types of events that trigger billing',
        help: 'E.g., "Meeting", "Review", "Revision"',
      },
      {
        name: 'rate_per_event_cents',
        label: 'Rate per Event (cents)',
        type: 'number',
        placeholder: '15000',
        help: '$150 per event',
        min: 0,
      },
    ],
    previewTemplate: (data) => {
      const rate = data.rate_per_event_cents ? `$${(data.rate_per_event_cents / 100).toFixed(2)}` : '$0';
      const events = data.event_types?.length ? ` (${data.event_types.length} events)` : '';
      return `${rate} per event${events}`;
    },
  },

  'travel': {
    type: 'travel',
    label: 'Travel Fees',
    description: 'Travel expenses and mileage',
    badge: {
      color: 'blue',
      text: 'Travel',
    },
    baseFields: [
      {
        name: 'currency',
        label: 'Currency',
        type: 'text',
        required: true,
        placeholder: 'USD',
        help: '3-letter ISO currency code',
      },
      {
        name: 'hourly_rate_cents',
        label: 'Travel Hourly Rate (cents)',
        type: 'number',
        description: 'Charged for travel time',
        placeholder: '10000',
        help: '$100/hour travel time',
        min: 0,
      },
      {
        name: 'mileage_rate_cents',
        label: 'Mileage Rate (cents/mile)',
        type: 'number',
        description: 'Charged per mile traveled',
        placeholder: '65',
        help: 'e.g., $0.65/mile',
        min: 0,
        step: 1,
      },
      {
        name: 'parking_charges',
        label: 'Parking & Tolls',
        type: 'checkbox',
        description: 'Pass through parking and toll charges',
      },
    ],
    previewTemplate: (data) => {
      const parts = [];
      if (data.hourly_rate_cents) {
        parts.push(`$${(data.hourly_rate_cents / 100).toFixed(2)}/hr`);
      }
      if (data.mileage_rate_cents) {
        parts.push(`$${(data.mileage_rate_cents / 100).toFixed(2)}/mi`);
      }
      if (data.parking_charges) {
        parts.push('+ parking/tolls');
      }
      return parts.length > 0 ? parts.join(', ') : 'Travel fees';
    },
  },
};

/**
 * Get all available rule types
 */
export const getRuleTypeOptions = () => {
  return Object.values(BILLING_RULE_TYPES).map((config) => ({
    label: config.label,
    value: config.type,
  }));
};

/**
 * Get configuration for a specific rule type
 */
export const getRuleTypeConfig = (ruleType: RuleType): RuleTypeConfig | undefined => {
  return BILLING_RULE_TYPES[ruleType];
};

/**
 * Get all fields for a rule type (base + conditional)
 */
export const getFieldsForRuleType = (ruleType: RuleType, conditions?: Record<string, boolean>) => {
  const config = getRuleTypeConfig(ruleType);
  if (!config) return [];

  const fields = [...config.baseFields];

  if (config.conditionalFields && conditions) {
    for (const [condition, conditionalFields] of Object.entries(config.conditionalFields)) {
      if (conditions[condition]) {
        fields.push(...conditionalFields);
      }
    }
  }

  return fields;
};

/**
 * Generate preview text for a rule
 */
export const generateRulePreview = (ruleType: RuleType, data: RulePreviewData): string => {
  const config = getRuleTypeConfig(ruleType);
  return config ? config.previewTemplate(data) : 'Unknown rule type';
};

/**
 * Get badge color and text for rule type
 */
export const getRuleTypeBadge = (ruleType: RuleType) => {
  const config = getRuleTypeConfig(ruleType);
  return config ? config.badge : { color: 'gray' as const, text: 'Unknown' };
};
