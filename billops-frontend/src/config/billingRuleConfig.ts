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
  /**
   * Condition to show this field. If not specified, always shown.
   * Examples: "has_revisions", "is_art_commission"
   */
  showWhen?: string;
  /**
   * The field name that this field depends on for visibility
   * Used for checkbox fields: dependsOn="field_name" means show if field_name is true
   */
  dependsOn?: string;
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
  /**
   * Additional fields that appear conditionally based on form values
   * Uses field dependencies and showWhen conditions
   */
  advancedFields?: RuleFieldConfig[];
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
    advancedFields: [
      {
        name: 'has_specialization',
        label: 'Specialization Rates',
        type: 'checkbox',
        description: 'Different rates for specialized work areas',
        help: 'Shows fields for premium rates on complex tasks',
      },
      {
        name: 'complex_work_rate_multiplier',
        label: 'Complex Work Multiplier',
        type: 'number',
        description: 'Rate multiplier for complex/specialized tasks',
        placeholder: '1.5',
        help: '1.5 = 50% premium on complex work',
        min: 1,
        step: 0.1,
        showWhen: 'has_specialization',
        dependsOn: 'has_specialization',
      },
      {
        name: 'after_hours_multiplier',
        label: 'After-Hours Multiplier',
        type: 'number',
        description: 'Rate multiplier for evenings/weekends',
        placeholder: '1.25',
        help: '1.25 = 25% premium for after-hours',
        min: 1,
        step: 0.1,
      },
      {
        name: 'emergency_fee_cents',
        label: 'Emergency Service Fee (cents)',
        type: 'number',
        description: 'Flat fee for emergency/rush requests',
        placeholder: '5000',
        help: '$50 emergency fee = 5000 cents (in addition to hourly rate)',
        min: 0,
      },
      {
        name: 'minimum_charge_hours',
        label: 'Minimum Charge (hours)',
        type: 'number',
        description: 'Minimum hours charged even for shorter sessions',
        placeholder: '1',
        help: 'Cannot charge less than this amount per billing session',
        min: 0.25,
        step: 0.25,
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
    advancedFields: [
      {
        name: 'is_art_commission',
        label: 'Art Commission Project',
        type: 'checkbox',
        description: 'Enable for design and art projects with revision tracking',
        help: 'Shows additional fields for managing revisions and deliverables',
      },
      {
        name: 'revisions_included',
        label: 'Revisions Included',
        type: 'number',
        description: 'Number of revision rounds included in the base fee',
        placeholder: '2',
        help: 'Additional revisions charged at the per-revision rate',
        min: 0,
        showWhen: 'is_art_commission',
        dependsOn: 'is_art_commission',
      },
      {
        name: 'revision_fee_cents',
        label: 'Per-Revision Fee (cents)',
        type: 'number',
        description: 'Cost for each revision beyond included amount',
        placeholder: '5000',
        help: '$50 per additional revision = 5000 cents',
        min: 0,
        showWhen: 'is_art_commission',
        dependsOn: 'is_art_commission',
      },
      {
        name: 'deposit_percent',
        label: 'Deposit Percentage',
        type: 'number',
        description: 'Initial deposit required before starting work',
        placeholder: '20',
        help: 'Percentage of total fee (e.g., 20 = 20%)',
        min: 0,
        max: 100,
        step: 5,
        showWhen: 'is_art_commission',
        dependsOn: 'is_art_commission',
      },
      {
        name: 'payment_schedule',
        label: 'Payment Schedule',
        type: 'text',
        description: 'Describe payment milestones',
        placeholder: 'Deposit on start, balance on delivery',
        help: 'e.g., "50% upfront, 50% at delivery" or "Deposit, Mid-project, Final"',
        showWhen: 'is_art_commission',
        dependsOn: 'is_art_commission',
      },
    ],
    previewTemplate: (data) => {
      const amount = data.rate_cents ? `$${(data.rate_cents / 100).toFixed(2)}` : '$0';
      const extras = [];
      if ((data as any).revisions_included) extras.push(`${(data as any).revisions_included} revisions`);
      if ((data as any).deposit_percent) extras.push(`${(data as any).deposit_percent}% deposit`);
      return extras.length > 0 ? `${amount} + ${extras.join(', ')}` : `${amount} flat fee`;
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
    advancedFields: [
      {
        name: 'support_tier_based',
        label: 'Support Tier Pricing',
        type: 'checkbox',
        description: 'Offer different service levels/VIP tiers',
        help: 'Shows fields for response time guarantees and priority support',
      },
      {
        name: 'response_time_hours',
        label: 'SLA Response Time (hours)',
        type: 'number',
        description: 'Guaranteed response time for this tier',
        placeholder: '4',
        help: 'Hours until guaranteed first response',
        min: 1,
        showWhen: 'support_tier_based',
        dependsOn: 'support_tier_based',
      },
      {
        name: 'priority_support_fee_cents',
        label: 'Premium Tier Upgrade (cents)',
        type: 'number',
        description: 'Additional monthly fee for priority/VIP support',
        placeholder: '50000',
        help: '$500 additional for priority = 50000 cents',
        min: 0,
        showWhen: 'support_tier_based',
        dependsOn: 'support_tier_based',
      },
      {
        name: 'includes_consultation',
        label: 'Monthly Consultation Call',
        type: 'checkbox',
        description: 'Include dedicated strategy session each month',
        showWhen: 'support_tier_based',
        dependsOn: 'support_tier_based',
      },
      {
        name: 'minimum_contract_months',
        label: 'Minimum Contract Length (months)',
        type: 'number',
        description: 'Minimum commitment required',
        placeholder: '3',
        help: 'Minimum number of months client must commit',
        min: 1,
        step: 1,
      },
      {
        name: 'annual_discount_percent',
        label: 'Annual Prepay Discount (%)',
        type: 'number',
        description: 'Discount for annual prepayment',
        placeholder: '10',
        help: 'Percentage discount if paying 12 months upfront',
        min: 0,
        max: 50,
        step: 5,
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
    advancedFields: [
      {
        name: 'is_notary_service',
        label: 'Notary Service',
        type: 'checkbox',
        description: 'Enable for notary public services with per-document fees',
        help: 'Shows fields for notarization stamps, exceptions, and verification',
      },
      {
        name: 'per_stamp_fee_cents',
        label: 'Per Stamp Fee (cents)',
        type: 'number',
        description: 'Additional fee per notary stamp/seal',
        placeholder: '500',
        help: '$5 per stamp = 500 cents',
        min: 0,
        showWhen: 'is_notary_service',
        dependsOn: 'is_notary_service',
      },
      {
        name: 'travel_fee_included',
        label: 'Travel Included',
        type: 'checkbox',
        description: 'Travel costs included in the per-item price',
        help: 'If unchecked, travel will be charged separately',
        showWhen: 'is_notary_service',
        dependsOn: 'is_notary_service',
      },
      {
        name: 'remote_notary_fee_cents',
        label: 'Remote Notary Premium (cents)',
        type: 'number',
        description: 'Additional fee for online/remote notarization',
        placeholder: '1000',
        help: '$10 premium for remote = 1000 cents',
        min: 0,
        showWhen: 'is_notary_service',
        dependsOn: 'is_notary_service',
      },
      {
        name: 'rush_processing_available',
        label: 'Rush Processing Available',
        type: 'checkbox',
        description: 'Offer expedited notary services',
        help: 'Allows charged at premium rates for quick turnaround',
        showWhen: 'is_notary_service',
        dependsOn: 'is_notary_service',
      },
      {
        name: 'rush_fee_multiplier',
        label: 'Rush Fee Multiplier',
        type: 'number',
        description: 'Multiplier applied to base fee for rush services',
        placeholder: '1.5',
        help: '1.5 = 50% premium on rush orders',
        min: 1,
        step: 0.1,
        showWhen: 'is_notary_service',
        dependsOn: 'is_notary_service',
      },
      {
        name: 'certification_type',
        label: 'Certification Type',
        type: 'text',
        description: 'Type of notary certification offered',
        placeholder: 'Acknowledged, Jurat, or Affidavit',
        help: 'e.g., "Acknowledged", "Jurat - Oath/Affirmation", "Copy Certification"',
        showWhen: 'is_notary_service',
        dependsOn: 'is_notary_service',
      },
    ],
    previewTemplate: (data) => {
      const rate = data.rate_cents ? `$${(data.rate_cents / 100).toFixed(2)}` : '$0';
      const item = data.item_description ? ` per ${data.item_description}` : ' per item';
      const extras = [];
      if ((data as any).per_stamp_fee_cents) extras.push(`+$${((data as any).per_stamp_fee_cents / 100).toFixed(2)}/stamp`);
      if ((data as any).remote_notary_fee_cents) extras.push(`+$${((data as any).remote_notary_fee_cents / 100).toFixed(2)} remote`);
      return extras.length > 0 ? `${rate}${item} (${extras.join(', ')})` : `${rate}${item}`;
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

  // Advanced fields are shown based on their own visibility conditions
  if (config.advancedFields) {
    fields.push(...config.advancedFields);
  }

  return fields;
};

/**
 * Get field visibility based on form data
 * Checks if a field's conditions are met given the current form values
 */
export const isFieldVisible = (field: RuleFieldConfig, formData: Record<string, any>): boolean => {
  // If no showWhen condition, always show
  if (!field.showWhen && !field.dependsOn) {
    return true;
  }

  // Check dependsOn (typically a checkbox that enables conditional fields)
  if (field.dependsOn) {
    return formData[field.dependsOn] === true;
  }

  // Check showWhen condition
  if (field.showWhen) {
    return formData[field.showWhen] === true;
  }

  return true;
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
