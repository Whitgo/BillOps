/**
 * Dynamic Billing Rule Form Component
 * Renders form fields based on the selected rule type configuration
 */

import React, { useMemo } from 'react';
import { Control, Controller, FieldValues, Path, useWatch } from 'react-hook-form';
import { AlertCircle, ChevronDown } from 'lucide-react';
import {
  getFieldsForRuleType,
  getRuleTypeConfig,
  RuleFieldConfig,
  RuleType,
  isFieldVisible,
} from '@/config/billingRuleConfig';
import clsx from 'clsx';
import type { BillingRuleFormData } from '@/schemas/billingRule';

type RuleFieldValue = string | number | boolean | string[] | undefined;

type FieldErrorMap = Partial<Record<string, { message?: string }>>;

interface RuleFieldInputProps {
  field: RuleFieldConfig;
  value: RuleFieldValue;
  onChange: (value: RuleFieldValue) => void;
  onBlur: () => void;
  error?: string;
  disabled?: boolean;
}

/**
 * Individual field renderer based on field type
 */
const RuleFieldInput: React.FC<RuleFieldInputProps> = ({
  field,
  value,
  onChange,
  onBlur,
  error,
  disabled,
}) => {
  switch (field.type) {
    case 'number':
      return (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <input
            type="number"
            value={value || ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
            onBlur={onBlur}
            placeholder={field.placeholder}
            min={field.min}
            max={field.max}
            step={field.step || 1}
            disabled={disabled}
            className={clsx(
              'w-full px-3 py-2 rounded-lg border transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              error
                ? 'border-red-300 bg-red-50'
                : 'border-gray-300 bg-white hover:border-gray-400'
            )}
          />
          {field.help && (
            <p className="text-xs text-gray-500 mt-1">{field.help}</p>
          )}
          {error && (
            <p className="text-sm text-red-600 mt-1">{error}</p>
          )}
        </div>
      );

    case 'text':
      return (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value || undefined)}
            onBlur={onBlur}
            placeholder={field.placeholder}
            disabled={disabled}
            className={clsx(
              'w-full px-3 py-2 rounded-lg border transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              error
                ? 'border-red-300 bg-red-50'
                : 'border-gray-300 bg-white hover:border-gray-400'
            )}
          />
          {field.help && (
            <p className="text-xs text-gray-500 mt-1">{field.help}</p>
          )}
          {error && (
            <p className="text-sm text-red-600 mt-1">{error}</p>
          )}
        </div>
      );

    case 'checkbox':
      return (
        <div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => onChange(e.target.checked)}
              onBlur={onBlur}
              disabled={disabled}
              className={clsx(
                'w-4 h-4 rounded border-gray-300 text-blue-600',
                'focus:ring-blue-500 cursor-pointer',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            />
            <span className="text-sm font-medium text-gray-700">{field.label}</span>
            {field.description && (
              <span className="text-xs text-gray-500">({field.description})</span>
            )}
          </label>
          {field.help && (
            <p className="text-xs text-gray-500 mt-1">{field.help}</p>
          )}
          {error && (
            <p className="text-sm text-red-600 mt-1">{error}</p>
          )}
        </div>
      );

    case 'date':
      return (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <input
            type="date"
            value={value || ''}
            onChange={(e) => onChange(e.target.value || undefined)}
            onBlur={onBlur}
            disabled={disabled}
            className={clsx(
              'w-full px-3 py-2 rounded-lg border transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              error
                ? 'border-red-300 bg-red-50'
                : 'border-gray-300 bg-white hover:border-gray-400'
            )}
          />
          {field.help && (
            <p className="text-xs text-gray-500 mt-1">{field.help}</p>
          )}
          {error && (
            <p className="text-sm text-red-600 mt-1">{error}</p>
          )}
        </div>
      );

    case 'array':
      return (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <textarea
            value={(value || []).join(', ')}
            onChange={(e) =>
              onChange(e.target.value ? e.target.value.split(',').map((s: string) => s.trim()) : undefined)
            }
            onBlur={onBlur}
            placeholder={field.placeholder || 'Comma-separated items'}
            disabled={disabled}
            rows={3}
            className={clsx(
              'w-full px-3 py-2 rounded-lg border transition-colors font-mono text-sm',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              error
                ? 'border-red-300 bg-red-50'
                : 'border-gray-300 bg-white hover:border-gray-400'
            )}
          />
          {field.help && (
            <p className="text-xs text-gray-500 mt-1">{field.help}</p>
          )}
          {error && (
            <p className="text-sm text-red-600 mt-1">{error}</p>
          )}
        </div>
      );

    default:
      return null;
  }
};

interface DynamicBillingRuleFormProps<T extends FieldValues = any> {
  ruleType: RuleType;
  control: Control<T>;
  errors?: FieldErrorMap;
  disabled?: boolean;
  showTypeDescription?: boolean;
  fieldPrefix?: string; // For nesting within compound billing rules, e.g., "blocks.0."
}

/**
 * Dynamic form component that renders fields based on rule type
 */
export const DynamicBillingRuleForm: React.FC<DynamicBillingRuleFormProps> = ({
  ruleType,
  control,
  errors = {},
  disabled = false,
  showTypeDescription = true,
  fieldPrefix = '',
}) => {
  const config = getRuleTypeConfig(ruleType);
  const fields = useMemo(() => getFieldsForRuleType(ruleType), [ruleType]);
  
  // Watch all form values to determine field visibility
  const formValues = useWatch({ control });

  if (!config) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-3 flex gap-2">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-red-800">Unknown rule type: {ruleType}</p>
      </div>
    );
  }

  // Separate base, advanced, and conditional fields
  const baseFields = config.baseFields || [];
  const advancedFields = config.advancedFields || [];
  
  // Base fields that enable visibility of advanced fields
  const visibilityToggles = advancedFields.filter(f => f.type === 'checkbox' && !f.dependsOn);

  return (
    <div className="space-y-4">
      {showTypeDescription && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
          <p className="text-sm text-gray-900 font-medium">{config.label}</p>
          <p className="text-xs text-gray-600 mt-1">{config.description}</p>
        </div>
      )}

      {/* Base Fields */}
      <div className="grid grid-cols-1 gap-4">
        {baseFields.map((field) => {
          const fieldName = (fieldPrefix + field.name) as Path<any>;
          return (
            <Controller
              key={field.name}
              name={fieldName}
              control={control}
              render={({ field: { value, onChange, onBlur } }) => (
                <div className="space-y-1">
                  {field.description && (
                    <p className="text-xs text-gray-600">{field.description}</p>
                  )}
                  <RuleFieldInput
                    field={field}
                    value={value as RuleFieldValue}
                    onChange={onChange}
                    onBlur={onBlur}
                    error={errors[field.name]?.message}
                    disabled={disabled}
                  />
                </div>
              )}
            />
          );
        })}
      </div>

      {/* Advanced Fields with Visibility Toggles */}
      {advancedFields.length > 0 && (
        <AdvancedFieldsSection
          fields={advancedFields}
          visibilityToggles={visibilityToggles}
          control={control}
          errors={errors}
          formValues={formValues}
          disabled={disabled}
          fieldPrefix={fieldPrefix}
        />
      )}
    </div>
  );
};

/**
 * Advanced Fields Section Component
 * Manages collapsible advanced fields with conditional visibility
 */
interface AdvancedFieldsSectionProps {
  fields: RuleFieldConfig[];
  visibilityToggles: RuleFieldConfig[];
  control: Control<any>;
  errors: any;
  formValues: any;
  disabled: boolean;
  fieldPrefix: string;
}

const AdvancedFieldsSection: React.FC<AdvancedFieldsSectionProps> = ({
  fields,
  visibilityToggles,
  control,
  errors,
  formValues,
  disabled,
  fieldPrefix,
}) => {
  const [expandedToggles, setExpandedToggles] = React.useState<Set<string>>(new Set());

  // Find which toggle fields are enabled
  const enabledToggles = visibilityToggles.filter(t => formValues?.[fieldPrefix + t.name] === true);

  // If at least one toggle is enabled, show that section as expanded
  React.useEffect(() => {
    const newExpanded = new Set(expandedToggles);
    enabledToggles.forEach(t => newExpanded.add(t.name));
    if (newExpanded.size !== expandedToggles.size) {
      setExpandedToggles(newExpanded);
    }
  }, [enabledToggles.length]);

  return (
    <div className="space-y-3 border-t pt-4">
      <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Advanced Options</p>
      
      {/* Visibility Toggle Buttons */}
      {visibilityToggles.map(toggle => {
        const fieldName = (fieldPrefix + toggle.name) as Path<any>;
        const isExpanded = expandedToggles.has(toggle.name);
        
        return (
          <div key={toggle.name}>
            <Controller
              name={fieldName}
              control={control}
              render={({ field }) => (
                <label className="flex items-center gap-2 p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={field.value || false}
                    onChange={(e) => {
                      field.onChange(e.target.checked);
                      if (e.target.checked) {
                        setExpandedToggles(new Set([...expandedToggles, toggle.name]));
                      } else {
                        const newSet = new Set(expandedToggles);
                        newSet.delete(toggle.name);
                        setExpandedToggles(newSet);
                      }
                    }}
                    disabled={disabled}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm text-gray-900">{toggle.label}</p>
                    {toggle.description && (
                      <p className="text-xs text-gray-500 mt-0.5">{toggle.description}</p>
                    )}
                  </div>
                  {field.value && (
                    <ChevronDown className={clsx(
                      'w-4 h-4 text-blue-600 flex-shrink-0 transition-transform',
                      isExpanded ? 'rotate-180' : ''
                    )} />
                  )}
                </label>
              )}
            />

            {/* Conditional Fields for this Toggle */}
            {isExpanded && (
              <div className="mt-2 ml-6 pl-3 border-l-2 border-blue-200 space-y-3">
                {fields
                  .filter(f => f.dependsOn === toggle.name && isFieldVisible(f, formValues))
                  .map(field => {
                    const fieldName = (fieldPrefix + field.name) as Path<any>;
                    return (
                      <Controller
                        key={field.name}
                        name={fieldName}
                        control={control}
                        render={({ field: { value, onChange, onBlur } }) => (
                          <div className="space-y-1">
                            {field.description && (
                              <p className="text-xs text-gray-600">{field.description}</p>
                            )}
                            <RuleFieldInput
                              field={field}
                              value={value as RuleFieldValue}
                              onChange={onChange}
                              onBlur={onBlur}
                              error={errors[field.name]?.message}
                              disabled={disabled}
                            />
                          </div>
                        )}
                      />
                    );
                  })}
              </div>
            )}
          </div>
        );
      })}

      {/* Non-toggle conditional fields (shown if their dependency is enabled) */}
      <div className="grid grid-cols-1 gap-4 mt-3">
        {fields
          .filter(f => !f.type || f.type !== 'checkbox')
          .filter(f => !visibilityToggles.find(t => t.name === f.name))
          .filter(f => isFieldVisible(f, formValues))
          .map(field => {
            const fieldName = (fieldPrefix + field.name) as Path<any>;
            return (
              <Controller
                key={field.name}
                name={fieldName}
                control={control}
                render={({ field: { value, onChange, onBlur } }) => (
                  <div className="space-y-1">
                    {field.description && (
                      <p className="text-xs text-gray-600">{field.description}</p>
                    )}
                    <RuleFieldInput
                      field={field}
                      value={value as RuleFieldValue}
                      onChange={onChange}
                      onBlur={onBlur}
                      error={errors[field.name]?.message}
                      disabled={disabled}
                    />
                  </div>
                )}
              />
            );
          })}
      </div>
    </div>
  );
};

export default DynamicBillingRuleForm;
