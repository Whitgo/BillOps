## Conditional Billing Fields - Quick Reference

Complete inventory of all conditional advanced fields currently implemented in the billing rule system.

---

## 📋 Fixed Fee Rules

### Art Commission Toggle
**Enable for:** Design and art projects with revision tracking

**Checkbox:** `is_art_commission`
**Description:** "Enable for design and art projects with revision tracking"

**Dependent Fields:**

| Field Name | Type | Example | Description |
|-----------|------|---------|-------------|
| `revisions_included` | number | 2 | Number of free revision rounds |
| `revision_fee_cents` | currency | $150 | Charge per revision beyond included |
| `deposit_percent` | number | 20 | Percentage of total fee required upfront |
| `payment_schedule` | text | 50% due upon approval, 50% on delivery | Milestone-based payment terms |

**Preview Impact:** 
- When enabled: `$500 fixed fee, 2 revisions, 20% deposit`
- When disabled: `$500 fixed fee`

**Real-world Example:**
```
Designer charges:
- Base fee: $500
- Client gets 2 rounds of revision
- Extra revisions: $75 each
- 20% deposit needed upfront
- Rest due on final delivery
```

---

## 💰 Per-Item Rules

### Notary Service Toggle
**Enable for:** Notary services with multiple fee types

**Checkbox:** `is_notary_service`
**Description:** "Enable for notary/witness services with stamp fees and rush options"

**Dependent Fields:**

| Field Name | Type | Example | Description |
|-----------|------|---------|-------------|
| `per_stamp_fee_cents` | currency | $500 | Additional charge per notary seal |
| `travel_fee_included` | checkbox | ☑ | Is travel included in base rate? |
| `remote_notary_fee_cents` | currency | $1000 | Premium for online notarization |
| `rush_processing_available` | checkbox | ☑ | Offer expedited service? |
| `rush_fee_multiplier` | number | 1.5 | Multiplier for rush (1.5 = 50% premium) |
| `certification_type` | select | Jurat / Acknowledgment / Both | Type of notarial certificate |

**Preview Impact:**
- When enabled: `$25/item, +$5/stamp, +$10 remote`
- When disabled: `$25/item`

**Real-world Example:**
```
Notary charges:
- Base fee: $25 per document
- Each notary seal: +$5
- Video/remote notarization: +$10
- Rush processing: 1.5x the total fee
- Can do jurats, acknowledgments, or both types
```

---

## ⏰ Hourly Rules

### Specialization Rates Toggle
**Enable for:** When you offer different rates for specialized/complex work

**Checkbox:** `has_specialization`
**Description:** "Enable for specialized work with custom rates and emergency fees"

**Dependent Fields:**

| Field Name | Type | Example | Description |
|-----------|------|---------|-------------|
| `complex_work_rate_multiplier` | number | 1.5 | Multiplier for complex work (1.5 = 50% premium) |
| `after_hours_multiplier` | number | 1.25 | Premium for work outside business hours |
| `emergency_fee_cents` | currency | $2500 | Flat additional fee for emergency requests |
| `minimum_charge_hours` | number | 2 | Minimum billable hours per project |

**Preview Impact:**
- When enabled: `$150/hr, complex work +50%, after-hours +25%`
- When disabled: `$150/hr`

**Real-world Example:**
```
Consultant charges:
- Standard rate: $150/hour
- Complex projects: 1.5x rate = $225/hour
- Evening/weekend: 1.25x rate = $187.50/hour
- Emergency request fee: $2,500 plus hourly
- Minimum 2-hour billing per project
```

---

## 💼 Retainer Rules

### Support Tier Toggle
**Enable for:** When retainer includes tiered SLA and priority support options

**Checkbox:** `support_tier_based`
**Description:** "Enable for support tiers with different response times and priority levels"

**Dependent Fields:**

| Field Name | Type | Example | Description |
|-----------|------|---------|-------------|
| `response_time_hours` | number | 2 | Maximum response time in hours |
| `priority_support_fee_cents` | currency | $5000 | Additional monthly fee for priority |
| `includes_consultation` | checkbox | ☑ | Monthly consultation call included? |
| `minimum_contract_months` | number | 12 | Minimum contract length in months |
| `annual_discount_percent` | number | 10 | Discount for annual prepayment (%) |

**Preview Impact:**
- When enabled: `$3000/mo, 160 hrs, 2h response time, 10% annual discount`
- When disabled: `$3000/mo, 160 hrs`

**Real-world Example:**
```
Support retainer:
- Base: $3,000/month (160 hours)
- Standard response: 24 hours
- Priority tier: +$5,000/month for 2-hour response
- Includes monthly strategy call
- 12-month minimum contract
- Annual prepayment saves 10%
```

---

## 🔍 Field Type Reference

### Text Input
- **Type:** `text`
- **Example:** Customer name, project description
- **Best for:** Short text fields

### Number Input
- **Type:** `number`
- **Example:** 2, 1.5, 50
- **Best for:** Quantities, multipliers, percentages

### Currency
- **Type:** `currency`
- **Example:** $500, $15.99
- **Notes:** Store as cents (500 cents = $5.00)

### Checkbox
- **Type:** `checkbox`
- **Example:** ☑ / ☐
- **Best for:** Yes/no decisions, enables/disables features

### Select (Dropdown)
- **Type:** `select`
- **Options:** Array of { value, label }
- **Best for:** Choosing from predefined choices

### Textarea
- **Type:** `textarea`
- **Example:** Multi-line text
- **Best for:** Longer descriptions

### Date
- **Type:** `date`
- **Format:** YYYY-MM-DD
- **Best for:** Date pickers

---

## 🎨 UI Behavior

### Advanced Options Section
- Located below base fields
- Collapsed by default
- User expands to see available options

### Toggle Appearance
- Checkbox appears in collapsible Advanced section
- Description shown next to checkbox
- Related fields indent below when checked

### Dependent Fields
- Appear only when parent toggle is checked
- Indented with left border for visual grouping
- Values preserved when hidden (can show/hide multiple times)

### Form Submission
- All fields (visible or hidden) included in submission
- Validation only applies to visible fields
- Backend receives all enabled/disabled toggles

---

## 💡 Usage Tips

### Tip 1: Enable Only What You Need
Don't check toggles for features you don't use. This keeps the form clean:
- ☑ Art Commission Project (if you sell art)
- ☐ Notary Service (if you're not a notary)
- ☑ Specialization Rates (if you have expert premium work)

### Tip 2: Preview Updates Automatically
The preview shows a summary of your configuration. As you fill in fields, the preview updates:
- Base rule: "Fixed Fee"
- After enabling Art Commission: "Fixed Fee, 2 revisions, 20% deposit"

### Tip 3: Test Your Configuration
Click around the form to see how fields appear and disappear:
1. Check the Art Commission checkbox
2. Notice how Revisions and Deposit fields appear
3. Uncheck it
4. Fields disappear (values still saved internally)

### Tip 4: Copy Existing Configurations
If you have a similar billing rule already configured, you can duplicate and modify it instead of building from scratch.

---

## 📊 Rule Types Overview

| Rule Type | When to Use | Toggle Option | Toggle Name |
|-----------|-----------|--------------|-------------|
| **Fixed Fee** | Flat-rate projects with clear scope | Art Commission | `is_art_commission` |
| **Per-Item** | Pricing per document, part, transaction | Notary Service | `is_notary_service` |
| **Hourly** | Billing by hours worked | Specialization Rates | `has_specialization` |
| **Retainer** | Monthly recurring work | Support Tiers | `support_tier_based` |
| **Session-Based** | Payment per meeting/session | *(coming soon)* | - |
| **Tiered** | Volume-based pricing | *(coming soon)* | - |
| **Event-Based** | Per-event or per-occurrence | *(coming soon)* | - |
| **Travel** | Hourly + mileage/distance | *(coming soon)* | - |

---

## 🛠️ For Developers

### Adding New Conditional Fields

To add conditional fields to a rule type:

1. **Open:** `src/config/billingRuleConfig.ts`
2. **Find:** Your rule type config
3. **Add:** `advancedFields` array with toggles and dependent fields
4. **Test:** Toggle in form, verify fields appear/disappear
5. **Update:** Preview template and validation schema
6. **Reference:** See `EXTENDING_CONDITIONAL_FIELDS.md` for detailed guide

### Key Properties

```typescript
{
  name: 'is_art_commission',           // Form field name (required)
  label: 'Art Commission Project',     // Display label (required)
  type: 'checkbox',                    // Field type (required)
  description: 'Enable for design...',  // Help text (recommended)
  dependsOn: 'parent_toggle',          // Only show when this is true (optional)
  showWhen: 'condition_flag',          // Alternative condition (optional)
  placeholder: 'Example text',         // Input hint (optional)
  options: [{ value, label }],         // For select type (optional)
}
```

### Configuration File Location
```
/workspaces/BillOps/billops-frontend/
└── src/config/billingRuleConfig.ts
```

### Component That Renders These Fields
```
/workspaces/BillOps/billops-frontend/
└── src/components/forms/DynamicBillingRuleForm.tsx
```

---

## 🧪 Testing Conditional Fields

### Manual Test Checklist
- [ ] Toggle appears correctly
- [ ] Dependent fields show when enabled
- [ ] Dependent fields hide when disabled
- [ ] Values are preserved when toggling
- [ ] Preview updates with new information
- [ ] Form submits successfully with fields enabled
- [ ] Form submits successfully with fields disabled

### Unit Tests Location
```
/workspaces/BillOps/billops-frontend/
└── src/__tests__/conditionalBillingFields.test.ts
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `CONDITIONAL_BILLING_FIELDS.md` | Comprehensive architecture documentation |
| `EXTENDING_CONDITIONAL_FIELDS.md` | Step-by-step guide to add new fields |
| `QUICK_REFERENCE.md` | **This file** - Quick lookup of all fields |
| `MULTI_BLOCK_BILLING_RULES.md` | Multiple rule blocks in one billing config |

---

## ❓ FAQ

**Q: What happens to field values when I disable a toggle?**
A: The fields disappear from view, but the values are preserved in the form. If you enable the toggle again, your values reappear.

**Q: Can I have multiple toggles at the same level?**
A: Yes! You can have multiple toggles in the Advanced section, and each has its own set of dependent fields.

**Q: Do I need to code anything to use these fields?**
A: No! The form automatically renders conditional fields based on the configuration. Just fill in the form and the frontend handles the rest.

**Q: How are these fields stored in the database?**
A: All fields are included in the billing rule record, including disabled ones. The backend uses the toggle value to determine what to apply when billing.

**Q: Can dependent fields have their own dependent fields?**
A: Not currently. Keep it to two levels (toggle → fields).

---

## 📞 Support

For detailed implementation:
→ See `EXTENDING_CONDITIONAL_FIELDS.md`

For architecture details:
→ See `CONDITIONAL_BILLING_FIELDS.md`

For multi-block rules:
→ See `MULTI_BLOCK_BILLING_RULES.md`

To see it in action:
→ Visit `/pages/ConditionalFieldsDemo.tsx`
