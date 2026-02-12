## Developer Guide: Adding Conditional Fields to Billing Rules

This guide explains how to add new conditional fields to any billing rule type. The conditional field system allows fields to appear/disappear based on checkbox toggles.

### Quick Start: Add a New Conditional Field

#### 1. Open `/src/config/billingRuleConfig.ts`

#### 2. Find the rule type you want to enhance (e.g., 'fixed', 'hourly', 'per-item')

#### 3. Add an `advancedFields` array if it doesn't exist

```typescript
const ruleTypeConfigs = {
  fixed: {
    label: 'Fixed Fee',
    // ... existing baseFields ...
    advancedFields: [
      // Add your fields here
    ],
  },
};
```

#### 4. Add a toggle field (checkbox) to enable the group

```typescript
{
  name: 'is_art_commission',                    // UI form field name
  label: 'Art Commission Project',              // Display label
  type: 'checkbox',                             // Always checkbox for toggles
  description: 'Enable for design projects with revision tracking',  // Helpful context
},
```

#### 5. Add dependent fields underneath

Fields that should only appear when the toggle is enabled:

```typescript
{
  name: 'revisions_included',
  label: 'Revisions Included',
  type: 'number',
  dependsOn: 'is_art_commission',  // KEY: Links to toggle above
  placeholder: '2',
  description: 'Number of free revision rounds included',
},
{
  name: 'revision_fee_cents',
  label: 'Per-Revision Fee',
  type: 'currency',
  dependsOn: 'is_art_commission',  // KEY: Links to toggle above
  description: 'Charge for revisions beyond the included amount',
},
```

### Complete Example: Notary Service for Per-Item Rules

Here's the full implementation for notary services:

```typescript
// In ruleTypeConfigs['per-item']
advancedFields: [
  // --- TOGGLE ---
  {
    name: 'is_notary_service',
    label: 'Notary Service',
    type: 'checkbox',
    description: 'Enable for notary/witness services with stamp fees',
  },

  // --- DEPENDENT FIELDS (show when is_notary_service = true) ---
  {
    name: 'per_stamp_fee_cents',
    label: 'Per Stamp Fee',
    type: 'currency',
    dependsOn: 'is_notary_service',
    placeholder: '500',      // $5.00
    description: 'Additional charge per notary seal/stamp',
  },
  {
    name: 'travel_fee_included',
    label: 'Travel Fee Included in Base Rate',
    type: 'checkbox',
    dependsOn: 'is_notary_service',
    description: 'If unchecked, travel costs are separate',
  },
  {
    name: 'remote_notary_fee_cents',
    label: 'Remote Notary Premium',
    type: 'currency',
    dependsOn: 'is_notary_service',
    placeholder: '1000',     // $10.00
    description: 'Extra charge for online/video notarization',
  },
  {
    name: 'rush_processing_available',
    label: 'Rush Processing Available',
    type: 'checkbox',
    dependsOn: 'is_notary_service',
    description: 'Enable expedited notarization service',
  },
  {
    name: 'rush_fee_multiplier',
    label: 'Rush Processing Fee Multiplier',
    type: 'number', 
    dependsOn: 'is_notary_service',
    placeholder: '1.5',
    description: 'Multiplier for rush services (e.g., 1.5 = 50% premium)',
  },
  {
    name: 'certification_type',
    label: 'Certification Type',
    type: 'select',
    dependsOn: 'is_notary_service',
    options: [
      { value: 'jurat', label: 'Jurat (signed and sworn)' },
      { value: 'acknowledgment', label: 'Acknowledgment' },
      { value: 'both', label: 'Both available' },
    ],
    description: 'Type of notarial certificate provided',
  },
],
```

### How It Works

#### The `dependsOn` Property

```typescript
{
  name: 'revisions_included',
  dependsOn: 'is_art_commission',  // This field only shows when is_art_commission = true
  // ...
}
```

- When `is_art_commission` checkbox is **UNCHECKED** (false): field is hidden
- When `is_art_commission` checkbox is **CHECKED** (true): field appears
- Form value is **always preserved** (not cleared when hidden)

#### The UI Behavior

When a user checks a toggle:

1. Toggle checkbox appears in "Advanced Options" section
2. When checked → all dependent fields appear indented below with left border
3. When unchecked → all dependent fields disappear
4. All form values are saved regardless of visibility

Example visual structure:
```
Advanced Options
├─ ☑ Art Commission Project
│  ├─ Revisions Included [2]
│  ├─ Per-Revision Fee [$150]
│  └─ Deposit Percentage [20%]
│
└─ ☐ Rush Processing Available
   └─ (fields hidden)
```

### Updating the Preview Template

The live preview shows a quick summary of the rule configuration. Update the `previewTemplate` to include conditional fields:

```typescript
previewTemplate: (values) => {
  const parts = [`$${(values.rate_cents / 100).toFixed(2)}`];
  
  // Add conditional details to preview
  if (values.is_art_commission) {
    parts.push(`${values.revisions_included || 0} revisions`);
    if (values.deposit_percent) {
      parts.push(`${values.deposit_percent}% deposit`);
    }
  }
  
  if (values.is_notary_service) {
    if (values.per_stamp_fee_cents) {
      parts.push(`+$${(values.per_stamp_fee_cents / 100).toFixed(2)}/stamp`);
    }
    if (values.remote_notary_fee_cents) {
      parts.push(`+$${(values.remote_notary_fee_cents / 100).toFixed(2)} remote`);
    }
  }
  
  return parts.join(', ');
},
```

Result: "Fixed Fee" becomes "Fixed Fee, 2 revisions, 20% deposit, +$5/stamp"

### Field Types Supported

| Type | Example | Notes |
|------|---------|-------|
| `text` | "Payment terms" | Text input |
| `number` | 2, 1.5 | Numeric input |
| `currency` | $500 | For cent-based fields use type='currency' |
| `checkbox` | ☑/☐ | Use for toggles and binary options |
| `select` | dropdown | Options array required |
| `textarea` | Long text | Multi-line text |
| `date` | 2024-01-15 | Date picker |

### Common Patterns

#### Pattern 1: Service Type Toggle + Settings

```typescript
// Toggle to enable special service
{ name: 'is_premium_service', type: 'checkbox', label: 'Premium Service' },

// Settings that appear when premium is enabled
{ name: 'premium_response_time', type: 'number', dependsOn: 'is_premium_service' },
{ name: 'premium_fee_percent', type: 'number', dependsOn: 'is_premium_service' },
{ name: 'priority_queue', type: 'checkbox', dependsOn: 'is_premium_service' },
```

#### Pattern 2: Complex Pricing Model

```typescript
// Base model selection
{ name: 'pricing_model', type: 'select', options: [...], label: 'Model' },

// Settings unique to each model
{ name: 'setup_fee', type: 'currency', showWhen: 'is_complex_model' },
{ name: 'monthly_maintenance', type: 'currency', showWhen: 'is_complex_model' },
```

#### Pattern 3: Multi-Level Options

```typescript
// Level 1: Toggle main feature
{ name: 'has_support', type: 'checkbox', label: 'Support Package' },

// Level 2: Choose support tier
{ name: 'support_tier', type: 'select', dependsOn: 'has_support' },

// Level 3: Tier-specific settings
{
  name: 'response_time',
  dependsOn: 'has_support',
  // Shows when has_support=true
  // Content depends on support_tier value
}
```

### Testing Your New Fields

#### 1. Manual Testing

1. Open the form for your rule type
2. Scroll to "Advanced Options"
3. Check the toggle
4. Verify fields appear with correct labels
5. Fill in values and save
6. Verify preview updates
7. Uncheck toggle
8. Verify fields disappear
9. Verify values are preserved (edit and check toggle again)

#### 2. Automated Testing

Add tests in `src/__tests__/conditionalBillingFields.test.ts`:

```typescript
describe('My New Service Type', () => {
  it('shows fields when toggle is enabled', () => {
    const formData = { is_my_service: true };
    
    const field = {
      name: 'my_setting',
      dependsOn: 'is_my_service',
      type: 'number',
    };
    
    expect(isFieldVisible(field, formData)).toBe(true);
  });
  
  it('hides fields when toggle is disabled', () => {
    const formData = { is_my_service: false };
    
    const field = {
      name: 'my_setting',
      dependsOn: 'is_my_service',
      type: 'number',
    };
    
    expect(isFieldVisible(field, formData)).toBe(false);
  });
});
```

### TypeScript/Schema Updates

If adding new currency fields, update the validation schema:

In `src/schemas/billingRule.ts`:

```typescript
export const billingRuleFormSchema = z.object({
  // ... existing fields ...
  
  // New fields with defaults
  is_my_service: z.boolean().default(false),
  my_setting_cents: z.number().default(0),
  my_text_setting: z.string().optional(),
});
```

### Best Practices

✅ **DO:**
- Use descriptive field names (`is_art_commission` not `flag1`)
- Add helpful descriptions for toggles
- Group related fields together
- Update preview template to show conditional details
- Keep dependent field names similar to toggle name
- Use clear, business-friendly labels

❌ **DON'T:**
- Mix multiple toggles at same level (confusing UI)
- Create deeply nested dependencies (>2 levels)
- Use cryptic abbreviated names
- Forget to update TypeScript schemas
- Leave preview template unchanged (users won't see new fields)

### Naming Conventions

Follow these patterns for consistency:

```typescript
// Toggles: Is_something or Has_something
is_art_commission
is_notary_service
has_specialization
support_tier_based

// Money amounts: field_cents (stored in cents, displayed as dollars)
revision_fee_cents      // $5 → 500
emergency_fee_cents     // $100 → 10000
priority_support_fee_cents

// Percentages: field_percent (0-100)
deposit_percent         // 20 for 20%
discount_percent
annual_discount_percent

// Multipliers: field_multiplier (1.0 = 100%, 1.5 = 150%)
complex_work_rate_multiplier
after_hours_multiplier
rush_fee_multiplier

// Counts: field_count or just number
revisions_included      // or revisions_count
minimum_contract_months
```

### Checklist for Adding New Conditional Fields

- [ ] Added toggle field to `advancedFields` array
- [ ] Added dependent fields with `dependsOn` property
- [ ] Added helpful descriptions to all fields
- [ ] Updated preview template to show new fields
- [ ] Updated TypeScript schema with new field definitions
- [ ] Set appropriate default values in schema
- [ ] Tested manual toggle on/off
- [ ] Verified form values are preserved
- [ ] Added unit tests for visibility logic
- [ ] Documented the new field use case
- [ ] Tested empty form scenario
- [ ] Tested form submission with conditional fields

### Common Issues & Solutions

**Issue: Fields don't appear when toggle is checked**
- Verify `dependsOn` property matches toggle name exactly (case-sensitive)
- Check TypeScript console for errors
- Clear browser cache and refresh

**Issue: Preview doesn't show conditional field values**
- Update `previewTemplate` function to include new fields
- Verify field names match exactly in preview template

**Issue: Field values disappear when toggling**
- This is expected behavior - fields are hidden, not cleared
- Values are preserved in form state
- Edit form again and toggle to see values reappear

**Issue: New fields not validating on form submission**
- Add required fields to validation schema in `billingRule.ts`
- Use `z.number().default(0)` for optional numeric fields
- Use `z.boolean().default(false)` for checkbox fields

### Getting Help

1. Check existing implementations (fixed, hourly, per-item, retainer)
2. Review tests in `src/__tests__/conditionalBillingFields.test.ts`
3. Check `CONDITIONAL_BILLING_FIELDS.md` for more details
4. Examine how `isFieldVisible()` works in `billingRuleConfig.ts`

### File Locations Reference

```
src/
├── config/
│   └── billingRuleConfig.ts          ← Add advancedFields here
├── schemas/
│   └── billingRule.ts                ← Update validation schema
├── components/forms/
│   └── DynamicBillingRuleForm.tsx    ← Already handles rendering
├── pages/
│   └── ConditionalFieldsDemo.tsx     ← Add usage example
└── __tests__/
    └── conditionalBillingFields.test.ts  ← Add your tests
```

That's it! The UI component (`DynamicBillingRuleForm`) automatically handles rendering conditional fields based on the configuration you add. No component changes needed.
