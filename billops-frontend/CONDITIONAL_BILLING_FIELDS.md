# Conditional Billing Rule Fields

## Overview

A powerful conditional field system that dynamically shows/hides form fields based on the rule type and user selections. This allows complex, context-specific billing scenarios without overwhelming users with irrelevant fields.

## Features

### 1. **Conditional Field Visibility**
- Fields appear only when relevant to the selected configuration
- Example: "Per-Stamp Fee" only shows for notary services
- Example: "Revisions Included" only shows for art commissions

### 2. **Smart Field Dependencies**
- Checkbox toggles enable/disable related fields
- Example: Enabling "Art Commission" shows revision tracking fields
- Example: Enabling "Specialization Rates" shows complex work multiplier

### 3. **Nested Conditional Logic**
- Multi-level field dependencies
- Example: "Remote Notary Premium" only shows if "Notary Service" is enabled AND notary fields are visible
- Supports cascading visibility rules

### 4. **Visual Hierarchy**
- **Base Fields**: Always visible, required for billing setup
- **Advanced Options**: Collapsible section with conditional visibility toggles
- **Dependent Fields**: Indented under their parent toggle

## Implementation Details

### Field Configuration

```typescript
interface RuleFieldConfig {
  name: string;                    // Field identifier
  label: string;                   // Display label
  type: 'number' | 'text' | ...;   // Input type
  // ... other properties
  
  // NEW: Conditional visibility
  showWhen?: string;               // Condition name for visibility
  dependsOn?: string;              // Parent field name for dependency
}
```

### Rule Type Configuration

Each rule type now has three field groups:

```typescript
interface RuleTypeConfig {
  baseFields: RuleFieldConfig[];       // Always shown
  conditionalFields?: Record<string, RuleFieldConfig[]>;  // Legacy pattern
  advancedFields?: RuleFieldConfig[];  // New: conditional advanced fields
}
```

### Visibility Logic

```typescript
function isFieldVisible(field: RuleFieldConfig, formData: Record<string, any>): boolean {
  // Shows if dependsOn field is true (checkbox checked)
  if (field.dependsOn) {
    return formData[field.dependsOn] === true;
  }
  
  // Shows if showWhen condition is true
  if (field.showWhen) {
    return formData[field.showWhen] === true;
  }
  
  return true;  // Always visible by default
}
```

## Use Cases by Rule Type

### Fixed Fee (Art Commissions)

**Base Fields**:
- Fee Amount
- Currency

**Advanced Toggle**: "Art Commission Project"

**Conditional Fields** (show when toggle enabled):
- Revisions Included ← Shows number of free revisions
- Per-Revision Fee ← Cost for additional revisions
- Deposit Percentage ← Required upfront payment
- Payment Schedule ← Milestone breakdown

**Preview Example**:
```
$500 + 2 revisions, 20% deposit
```

### Per Item (Notary Services)

**Base Fields**:
- Price per Item
- Currency
- Item Description

**Advanced Toggle**: "Notary Service"

**Conditional Fields** (show when toggle enabled):
- Per Stamp Fee ← Per seal/stamp charge
- Travel Fee Included ← Toggle to exclude travel
- Remote Notary Premium ← Extra for online notarization
- Rush Processing Available ← Toggle for expedited service
- Rush Fee Multiplier ← Premium for rush (depends on toggle)
- Certification Type ← Jurat, Acknowledged, etc.

**Preview Example**:
```
$25 per document (+$5/stamp, +$10 remote)
```

### Hourly Rate (Specializations)

**Base Fields**:
- Hourly Rate
- Currency
- Rounding Increment
- Overtime Multiplier
- Cap Hours

**Advanced Toggle**: "Specialization Rates"

**Conditional Fields** (show when toggle enabled):
- Complex Work Multiplier ← Premium for complex tasks
- After-Hours Multiplier ← Evening/weekend premium
- Emergency Fee ← Rush/emergency flat fee
- Minimum Charge Hours ← Minimum billable per session

**Preview Example**:
```
$150/hr (1.5x OT) - 160h cap
```

### Retainer (Support Tiers)

**Base Fields**:
- Monthly Retainer
- Currency
- Included Hours
- Overtime Multiplier

**Advanced Toggle**: "Support Tier Pricing"

**Conditional Fields** (show when toggle enabled):
- Response Time SLA ← Hours to respond
- Priority Support Fee ← Upgrade cost for tier
- Monthly Consultation ← Dedicated strategy call
- Minimum Contract Months ← Lock-in period
- Annual Prepay Discount ← Bulk discount

**Preview Example**:
```
$3000/month (160h, 2h SLA response, 10% annual discount)
```

## Component Behavior

### DynamicBillingRuleForm

1. **Watch Form Values**:
   ```tsx
   const formValues = useWatch({ control });
   ```

2. **Separate Field Groups**:
   ```tsx
   const baseFields = config.baseFields;
   const advancedFields = config.advancedFields;
   const visibilityToggles = advancedFields.filter(f => f.type === 'checkbox' && !f.dependsOn);
   ```

3. **Render Advanced Fields Section**:
   ```tsx
   <AdvancedFieldsSection
     fields={advancedFields}
     visibilityToggles={visibilityToggles}
     formValues={formValues}
     // ...
   />
   ```

### AdvancedFieldsSection

1. **Track Expanded Toggles**:
   ```tsx
   const [expandedToggles, setExpandedToggles] = useState<Set<string>>();
   ```

2. **Render Toggle Buttons**:
   - Styled checkbox with label and description
   - Shows chevron icon when expanded
   - Updates expanded state on change

3. **Conditionally Render Dependent Fields**:
   ```tsx
   fields
     .filter(f => f.dependsOn === toggle.name)
     .filter(f => isFieldVisible(f, formValues))
     .map(field => <RuleFieldInput ... />)
   ```

4. **Indented Layout**:
   ```tsx
   <div className="ml-6 pl-3 border-l-2 border-blue-200">
     {/* Dependent fields here */}
   </div>
   ```

## Visual Design

### Advanced Options Section

```
Advanced Options
────────────────────────────────────

☑ Art Commission Project
  Enable for design and art projects with revision tracking

  Revisions Included: [___] 
  Per-Revision Fee: [_____] cents
  Deposit Percentage: [__]%
  Payment Schedule: [_________________]

☐ Other Option
  Description here
```

### Interaction Flow

1. User selects rule type → Base fields appear
2. User scrolls to "Advanced Options" section
3. User checks/unchecks toggles → Dependent fields appear/hide
4. Dependent field values appear in live preview
5. User submits form with all relevant data

## Data Structure

### Form Data Shape

```typescript
{
  // Base fields
  project_id: "uuid",
  rule_type: "fixed",
  rate_cents: 50000,
  currency: "USD",
  
  // Advanced fields (only if enabled)
  is_art_commission: true,
  revisions_included: 2,
  revision_fee_cents: 5000,
  deposit_percent: 20,
  payment_schedule: "Deposit on start, balance on delivery",
  
  // Global fields
  effective_from: "2026-02-12",
  effective_to: null,
  meta: {...}
}
```

### API Submission

All fields (including conditionally shown ones) are included in form submission:

```json
{
  "project_id": "...",
  "rule_type": "fixed",
  "rate_cents": 50000,
  "currency": "USD",
  "is_art_commission": true,
  "revisions_included": 2,
  "revision_fee_cents": 5000,
  "deposit_percent": 20,
  "payment_schedule": "Deposit on start, balance on delivery",
  "effective_from": "2026-02-12"
}
```

## Usage Examples

### Adding a New Conditional Field

In `billingRuleConfig.ts`:

```typescript
advancedFields: [
  {
    name: 'enable_feature',
    label: 'Enable Feature Name',
    type: 'checkbox',
    description: 'What this feature enables',
    help: 'Relevant help text',
  },
  {
    name: 'feature_param_1',
    label: 'Feature Parameter',
    type: 'number',
    description: 'Configure the feature',
    dependsOn: 'enable_feature',  // Shows when enable_feature is true
  },
]
```

### Checking Field Visibility in Custom Logic

```typescript
import { isFieldVisible } from '@/config/billingRuleConfig';

const field = advancedFields[0];
const visible = isFieldVisible(field, formValues);

if (visible) {
  // Include in preview
}
```

## Advanced Features

### Cascading Dependencies

Fields can depend on other fields that themselves depend on toggles:

```typescript
advancedFields: [
  {
    name: 'tier_pricing',
    label: 'Tier-Based Pricing',
    type: 'checkbox',
  },
  {
    name: 'response_time',
    label: 'Response Time SLA',
    type: 'number',
    dependsOn: 'tier_pricing',  // Show if tier_pricing enabled
  },
  {
    name: 'critical_response_time',
    label: 'Critical Priority SLA',
    type: 'number',
    dependsOn: 'tier_pricing',  // Also depends on tier_pricing
  },
]
```

### Multiple Toggles

Different toggles can be independent or work together:

```typescript
// Both can be enabled simultaneously
is_art_commission: true
support_tier_based: false

// Creates different field sets
```

### Conditional Preview

Preview template reflects enabled advanced fields:

```typescript
previewTemplate: (data) => {
  const amount = `$${(data.rate_cents / 100).toFixed(2)}`;
  const extras = [];
  
  if (data.is_art_commission) {
    extras.push(`${data.revisions_included} revisions`);
    extras.push(`${data.deposit_percent}% deposit`);
  }
  
  return extras.length > 0 
    ? `${amount} + ${extras.join(', ')}`
    : `${amount} flat fee`;
};
```

## Browser Compatibility

- Chrome/Edge: Full support (ChevronDown animation)
- Firefox: Full support
- Safari: Full support
- Mobile: Fully responsive

## Performance

- **Lazy Rendering**: Fields only rendered if visible
- **Efficient Watching**: Single `useWatch` hook watches all form values
- **Smart Updates**: Re-renders only affected fields on dependency changes
- **Memory Efficient**: Expanded state tracked in Set for O(1) lookups

## Testing Guide

### Test Scenarios

1. **Toggle Visibility**:
   - Enable toggle → conditional fields appear
   - Disable toggle → conditional fields disappear
   - Values preserved on toggle

2. **Dependency Chain**:
   - Parent toggle disabled → all dependent fields hidden
   - Parent toggle enabled → dependent fields visible
   - Disable parent → dependent values preserved

3. **Multiple Toggles**:
   - Enable multiple toggles simultaneously
   - Each shows its own dependent fields
   - Fields from different toggles don't interfere

4. **Form Submission**:
   - Include all visible field values
   - Include hidden but enabled field values
   - Validation respects conditional requirements

5. **Live Preview**:
   - Preview updates when advanced fields change
   - Shows detailed summary with all enabled components
   - Updates in real-time

## Known Limitations

- Circular dependencies not supported (would cause infinite loops)
- Maximum nesting depth: 2 levels recommended
- Fields always appear in declaration order
- No dynamic show/hide animation (instant visibility change)

## Future Enhancements

1. **Drag & Drop Field Reordering**: Customize field order per rule type
2. **Custom Validators**: Conditional validation based on enabled fields
3. **Field Groups**: Organize conditionals into tabbed sections
4. **Multi-Select Conditions**: Field visible if ANY of multiple conditions true
5. **Template Variants**: Different advanced fields per industry/profession
6. **Field Dependencies UI**: Visual dependency graph builder

---

**Status**: ✅ Complete - Ready for production use
