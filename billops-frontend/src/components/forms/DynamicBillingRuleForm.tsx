/**
 * Dynamic Billing Rule Form Component
 * Renders form fields based on the selected rule type configuration
 */

import React, { useMemo } from 'react';
import { Control, Controller } from 'react-hook-form';
import { AlertCircle } from 'lucide-react';
import {
  getFieldsForRuleType,
  getRuleTypeConfig,
  RuleFieldConfig,
  RuleType,
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

interface DynamicBillingRuleFormProps {
  ruleType: RuleType;
  control: Control<BillingRuleFormData>;
  errors?: FieldErrorMap;
  disabled?: boolean;
  showTypeDescription?: boolean;
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
}) => {
  const config = getRuleTypeConfig(ruleType);
  const fields = useMemo(() => getFieldsForRuleType(ruleType), [ruleType]);

  if (!config) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-3 flex gap-2">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-red-800">Unknown rule type: {ruleType}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showTypeDescription && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
          <p className="text-sm text-gray-900 font-medium">{config.label}</p>
          <p className="text-xs text-gray-600 mt-1">{config.description}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {fields.map((field) => (
          <Controller
            key={field.name}
            name={field.name}
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
        ))}
      </div>
    </div>
  );
};

export default DynamicBillingRuleForm;
