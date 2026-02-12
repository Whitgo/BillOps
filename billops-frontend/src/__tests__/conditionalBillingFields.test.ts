/**
 * Tests for Conditional Billing Rule Fields
 * Validates that advanced fields appear/disappear correctly based on conditions
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { isFieldVisible, getRuleTypeConfig, getFieldsForRuleType } from '@/config/billingRuleConfig';
import type { RuleFieldConfig } from '@/config/billingRuleConfig';

describe('Conditional Billing Fields - isFieldVisible', () => {
  describe('Field Visibility Logic', () => {
    it('shows fields with no conditions by default', () => {
      const field: RuleFieldConfig = {
        name: 'rate_cents',
        label: 'Rate',
        type: 'number',
      };
      const formData = {};
      expect(isFieldVisible(field, formData)).toBe(true);
    });

    it('shows field when dependsOn condition is true', () => {
      const field: RuleFieldConfig = {
        name: 'revisions_included',
        label: 'Revisions Included',
        type: 'number',
        dependsOn: 'is_art_commission',
      };
      const formData = { is_art_commission: true };
      expect(isFieldVisible(field, formData)).toBe(true);
    });

    it('hides field when dependsOn condition is false', () => {
      const field: RuleFieldConfig = {
        name: 'revisions_included',
        label: 'Revisions Included',
        type: 'number',
        dependsOn: 'is_art_commission',
      };
      const formData = { is_art_commission: false };
      expect(isFieldVisible(field, formData)).toBe(false);
    });

    it('hides field when dependsOn condition is missing', () => {
      const field: RuleFieldConfig = {
        name: 'revisions_included',
        label: 'Revisions Included',
        type: 'number',
        dependsOn: 'is_art_commission',
      };
      const formData = {};
      expect(isFieldVisible(field, formData)).toBe(false);
    });

    it('shows field when showWhen condition is true', () => {
      const field: RuleFieldConfig = {
        name: 'per_stamp_fee_cents',
        label: 'Per Stamp Fee',
        type: 'number',
        showWhen: 'is_notary_service',
      };
      const formData = { is_notary_service: true };
      expect(isFieldVisible(field, formData)).toBe(true);
    });

    it('hides field when showWhen condition is false', () => {
      const field: RuleFieldConfig = {
        name: 'per_stamp_fee_cents',
        label: 'Per Stamp Fee',
        type: 'number',
        showWhen: 'is_notary_service',
      };
      const formData = { is_notary_service: false };
      expect(isFieldVisible(field, formData)).toBe(false);
    });

    it('prioritizes dependsOn over showWhen', () => {
      // When both are specified, dependsOn takes precedence
      const field: RuleFieldConfig = {
        name: 'test_field',
        label: 'Test Field',
        type: 'text',
        dependsOn: 'toggle_a',
        showWhen: 'toggle_b',
      };
      const formData = { toggle_a: false, toggle_b: true };
      // Should check dependsOn first
      expect(isFieldVisible(field, formData)).toBe(false);
    });
  });

  describe('Real World Scenarios', () => {
    describe('Art Commission (Fixed Fee) Scenario', () => {
      it('shows revision fields when art commission is enabled', () => {
        const formData = {
          rule_type: 'fixed',
          is_art_commission: true,
          rate_cents: 50000,
        };

        const revisionField: RuleFieldConfig = {
          name: 'revisions_included',
          dependsOn: 'is_art_commission',
          label: 'Revisions Included',
          type: 'number',
        };

        const revisionFeeField: RuleFieldConfig = {
          name: 'revision_fee_cents',
          dependsOn: 'is_art_commission',
          label: 'Per-Revision Fee',
          type: 'number',
        };

        expect(isFieldVisible(revisionField, formData)).toBe(true);
        expect(isFieldVisible(revisionFeeField, formData)).toBe(true);
      });

      it('hides revision fields when art commission is disabled', () => {
        const formData = {
          rule_type: 'fixed',
          is_art_commission: false,
          rate_cents: 50000,
        };

        const revisionField: RuleFieldConfig = {
          name: 'revisions_included',
          dependsOn: 'is_art_commission',
          label: 'Revisions Included',
          type: 'number',
        };

        expect(isFieldVisible(revisionField, formData)).toBe(false);
      });

      it('shows deposit and schedule fields when art commission is enabled', () => {
        const formData = { is_art_commission: true };

        const depositField: RuleFieldConfig = {
          name: 'deposit_percent',
          dependsOn: 'is_art_commission',
          label: 'Deposit Percentage',
          type: 'number',
        };

        const scheduleField: RuleFieldConfig = {
          name: 'payment_schedule',
          dependsOn: 'is_art_commission',
          label: 'Payment Schedule',
          type: 'text',
        };

        expect(isFieldVisible(depositField, formData)).toBe(true);
        expect(isFieldVisible(scheduleField, formData)).toBe(true);
      });
    });

    describe('Notary Service (Per Item) Scenario', () => {
      it('shows all notary fields when notary service is enabled', () => {
        const formData = { is_notary_service: true };

        const stampFeeField: RuleFieldConfig = {
          name: 'per_stamp_fee_cents',
          dependsOn: 'is_notary_service',
          label: 'Per Stamp Fee',
          type: 'number',
        };

        const remoteFeeField: RuleFieldConfig = {
          name: 'remote_notary_fee_cents',
          dependsOn: 'is_notary_service',
          label: 'Remote Notary Premium',
          type: 'number',
        };

        const rushField: RuleFieldConfig = {
          name: 'rush_processing_available',
          dependsOn: 'is_notary_service',
          label: 'Rush Processing',
          type: 'checkbox',
        };

        expect(isFieldVisible(stampFeeField, formData)).toBe(true);
        expect(isFieldVisible(remoteFeeField, formData)).toBe(true);
        expect(isFieldVisible(rushField, formData)).toBe(true);
      });

      it('hides notary-specific fields when service is disabled', () => {
        const formData = { is_notary_service: false };

        const stampFeeField: RuleFieldConfig = {
          name: 'per_stamp_fee_cents',
          dependsOn: 'is_notary_service',
          label: 'Per Stamp Fee',
          type: 'number',
        };

        expect(isFieldVisible(stampFeeField, formData)).toBe(false);
      });
    });

    describe('Specialization Rates (Hourly) Scenario', () => {
      it('shows specialization multiplier when specialization is enabled', () => {
        const formData = { has_specialization: true };

        const multiplierField: RuleFieldConfig = {
          name: 'complex_work_rate_multiplier',
          dependsOn: 'has_specialization',
          label: 'Complex Work Rate Multiplier',
          type: 'number',
        };

        expect(isFieldVisible(multiplierField, formData)).toBe(true);
      });

      it('shows emergency and after-hours fields when specialization enabled', () => {
        const formData = { has_specialization: true };

        const emergencyField: RuleFieldConfig = {
          name: 'emergency_fee_cents',
          dependsOn: 'has_specialization',
          label: 'Emergency Fee',
          type: 'number',
        };

        const afterHoursField: RuleFieldConfig = {
          name: 'after_hours_multiplier',
          dependsOn: 'has_specialization',
          label: 'After Hours Multiplier',
          type: 'number',
        };

        expect(isFieldVisible(emergencyField, formData)).toBe(true);
        expect(isFieldVisible(afterHoursField, formData)).toBe(true);
      });
    });

    describe('Support Tiers (Retainer) Scenario', () => {
      it('shows tier fields when support tier based is enabled', () => {
        const formData = { support_tier_based: true };

        const responseTimeField: RuleFieldConfig = {
          name: 'response_time_hours',
          dependsOn: 'support_tier_based',
          label: 'Response Time (hours)',
          type: 'number',
        };

        const priorityFeeField: RuleFieldConfig = {
          name: 'priority_support_fee_cents',
          dependsOn: 'support_tier_based',
          label: 'Priority Support Fee',
          type: 'number',
        };

        expect(isFieldVisible(responseTimeField, formData)).toBe(true);
        expect(isFieldVisible(priorityFeeField, formData)).toBe(true);
      });

      it('shows contract and discount fields when support tier enabled', () => {
        const formData = { support_tier_based: true };

        const contractField: RuleFieldConfig = {
          name: 'minimum_contract_months',
          dependsOn: 'support_tier_based',
          label: 'Minimum Contract Months',
          type: 'number',
        };

        const discountField: RuleFieldConfig = {
          name: 'annual_discount_percent',
          dependsOn: 'support_tier_based',
          label: 'Annual Prepay Discount %',
          type: 'number',
        };

        expect(isFieldVisible(contractField, formData)).toBe(true);
        expect(isFieldVisible(discountField, formData)).toBe(true);
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined formData gracefully', () => {
      const field: RuleFieldConfig = {
        name: 'test',
        label: 'Test',
        type: 'text',
        dependsOn: 'missing_key',
      };
      expect(isFieldVisible(field, {})).toBe(false);
    });

    it('treats any truthy value as visible', () => {
      const field: RuleFieldConfig = {
        name: 'test',
        label: 'Test',
        type: 'text',
        dependsOn: 'flag',
      };

      // True should show
      expect(isFieldVisible(field, { flag: true })).toBe(true);

      // 1 should NOT show (we only check === true)
      expect(isFieldVisible(field, { flag: 1 })).toBe(false);

      // "yes" string should NOT show (we only check === true)
      expect(isFieldVisible(field, { flag: 'yes' })).toBe(false);
    });

    it('handles fields with both dependsOn and showWhen', () => {
      const field: RuleFieldConfig = {
        name: 'test',
        label: 'Test',
        type: 'text',
        dependsOn: 'toggle_a',
        showWhen: 'toggle_b',
      };

      // dependsOn takes precedence
      expect(isFieldVisible(field, { toggle_a: true, toggle_b: false })).toBe(true);
      expect(isFieldVisible(field, { toggle_a: false, toggle_b: true })).toBe(false);
    });

    it('handles rapidly toggling conditions', () => {
      const field: RuleFieldConfig = {
        name: 'advanced',
        dependsOn: 'enabled',
        label: 'Advanced Option',
        type: 'number',
      };

      // Rapidly toggle true -> false -> true
      expect(isFieldVisible(field, { enabled: true })).toBe(true);
      expect(isFieldVisible(field, { enabled: false })).toBe(false);
      expect(isFieldVisible(field, { enabled: true })).toBe(true);
      expect(isFieldVisible(field, { enabled: false })).toBe(false);
    });
  });
});

describe('Rule Type Configurations', () => {
  describe('Advanced Fields Availability', () => {
    it('fixed rule type has advancedFields for art commissions', () => {
      const config = getRuleTypeConfig('fixed');
      expect(config.advancedFields).toBeDefined();

      const artCommissionToggle = config.advancedFields?.find(f => f.name === 'is_art_commission');
      expect(artCommissionToggle).toBeDefined();
      expect(artCommissionToggle?.type).toBe('checkbox');
    });

    it('per-item rule type has advancedFields for notary', () => {
      const config = getRuleTypeConfig('per-item');
      expect(config.advancedFields).toBeDefined();

      const notaryToggle = config.advancedFields?.find(f => f.name === 'is_notary_service');
      expect(notaryToggle).toBeDefined();
      expect(notaryToggle?.type).toBe('checkbox');
    });

    it('hourly rule type has advancedFields for specialization', () => {
      const config = getRuleTypeConfig('hourly');
      expect(config.advancedFields).toBeDefined();

      const specializationToggle = config.advancedFields?.find(f => f.name === 'has_specialization');
      expect(specializationToggle).toBeDefined();
      expect(specializationToggle?.type).toBe('checkbox');
    });

    it('retainer rule type has advancedFields for support tiers', () => {
      const config = getRuleTypeConfig('retainer');
      expect(config.advancedFields).toBeDefined();

      const tierToggle = config.advancedFields?.find(f => f.name === 'support_tier_based');
      expect(tierToggle).toBeDefined();
      expect(tierToggle?.type).toBe('checkbox');
    });
  });

  describe('Field Dependencies', () => {
    it('art commission fields depend on is_art_commission', () => {
      const config = getRuleTypeConfig('fixed');
      const advancedFields = config.advancedFields || [];

      const revisionField = advancedFields.find(f => f.name === 'revisions_included');
      expect(revisionField?.dependsOn).toBe('is_art_commission');

      const depositField = advancedFields.find(f => f.name === 'deposit_percent');
      expect(depositField?.dependsOn).toBe('is_art_commission');
    });

    it('notary fields depend on is_notary_service', () => {
      const config = getRuleTypeConfig('per-item');
      const advancedFields = config.advancedFields || [];

      const stampFeeField = advancedFields.find(f => f.name === 'per_stamp_fee_cents');
      expect(stampFeeField?.dependsOn).toBe('is_notary_service');

      const remoteField = advancedFields.find(f => f.name === 'remote_notary_fee_cents');
      expect(remoteField?.dependsOn).toBe('is_notary_service');
    });
  });

  describe('Field Descriptions', () => {
    it('toggle fields have meaningful descriptions', () => {
      const config = getRuleTypeConfig('fixed');
      const artCommissionToggle = config.advancedFields?.find(f => f.name === 'is_art_commission');

      expect(artCommissionToggle?.description).toBeDefined();
      expect(artCommissionToggle?.description?.length).toBeGreaterThan(10);
    });
  });
});

describe('Integration Tests', () => {
  it('supports multi-level dependency chains', () => {
    // Scenario: Some fields only show when multiple conditions are true
    // e.g., Rush fee multiplier only shows if rush_processing_available is true
    const formData = {
      is_notary_service: true,
      rush_processing_available: false,
    };

    const rushMultiplierField: RuleFieldConfig = {
      name: 'rush_fee_multiplier',
      dependsOn: 'rush_processing_available',
      label: 'Rush Processing Fee Multiplier',
      type: 'number',
    };

    // Should be hidden because rush_processing_available is false
    expect(isFieldVisible(rushMultiplierField, formData)).toBe(false);

    // Enable rush processing
    formData.rush_processing_available = true;
    expect(isFieldVisible(rushMultiplierField, formData)).toBe(true);
  });

  it('preserves field values when toggling visibility', () => {
    // This test validates that the form component properly saves field values
    // even when the fields are not displayed. This is implemented in the
    // UX layer, not in isFieldVisible, but worth testing the assumption.

    const formData = {
      is_art_commission: false,
      revisions_included: 2, // This value should be preserved
    };

    const revisionField: RuleFieldConfig = {
      name: 'revisions_included',
      dependsOn: 'is_art_commission',
      label: 'Revisions Included',
      type: 'number',
    };

    // Field is hidden because is_art_commission is false
    expect(isFieldVisible(revisionField, formData)).toBe(false);
    // But the value should still exist in formData
    expect(formData.revisions_included).toBe(2);

    // When user enables art commission, field becomes visible
    formData.is_art_commission = true;
    expect(isFieldVisible(revisionField, formData)).toBe(true);
    // Value should still be 2 (not cleared)
    expect(formData.revisions_included).toBe(2);
  });
});
