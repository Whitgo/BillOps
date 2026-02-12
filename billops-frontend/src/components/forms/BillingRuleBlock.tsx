/**
 * Single Billing Rule Block Component
 * Represents one block within a compound billing rule
 */

import React from 'react';
import { Control, Controller, FieldArrayWithId } from 'react-hook-form';
import { Trash2, GripVertical, Eye, EyeOff, ChevronUp, ChevronDown } from 'lucide-react';
import { DynamicBillingRuleForm } from './DynamicBillingRuleForm';
import { Button } from '@/components/ui';
import type { RuleType } from '@/config/billingRuleConfig';
import type { CompoundBillingRuleFormData } from '@/schemas/compoundBillingRule';
import { generateRulePreview } from '@/config/billingRuleConfig';
import clsx from 'clsx';

interface BillingRuleBlockProps {
  field: FieldArrayWithId<CompoundBillingRuleFormData, 'blocks', 'id'>;
  index: number;
  totalBlocks: number;
  control: Control<CompoundBillingRuleFormData>;
  errors?: Record<string, any>;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onToggle: () => void;
}

export const BillingRuleBlock: React.FC<BillingRuleBlockProps> = ({
  field,
  index,
  totalBlocks,
  control,
  errors = {},
  onRemove,
  onMoveUp,
  onMoveDown,
  onToggle,
}) => {
  const blockErrors = errors[index] || {};
  const enabled = field.enabled ?? true;
  const ruleType = field.rule_type as RuleType;

  return (
    <div className={clsx(
      'rounded-lg border-2 p-4 transition-all',
      enabled
        ? 'border-blue-300 bg-white'
        : 'border-gray-300 bg-gray-50 opacity-75'
    )}>
      {/* Block Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3 flex-1">
          <GripVertical className="w-5 h-5 text-gray-400 cursor-grab active:cursor-grabbing" />
          <div className="flex-1">
            <div className="text-sm font-semibold text-gray-900">
              Block {index + 1}: {field.rule_type}
              {!enabled && <span className="ml-2 text-xs text-gray-500">(Disabled)</span>}
            </div>
            {/* Live Preview */}
            <div className="text-xs text-gray-600 mt-1">
              {generateRulePreview(ruleType, field)}
            </div>
          </div>
        </div>

        {/* Block Controls */}
        <div className="flex items-center gap-1">
          {/* Toggle Enable/Disable */}
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={onToggle}
            title={enabled ? 'Disable block' : 'Enable block'}
            className="text-gray-500 hover:text-gray-700"
          >
            {enabled ? (
              <Eye className="w-4 h-4" />
            ) : (
              <EyeOff className="w-4 h-4" />
            )}
          </Button>

          {/* Move Up */}
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={onMoveUp}
            disabled={index === 0}
            title="Move block up"
            className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
          >
            <ChevronUp className="w-4 h-4" />
          </Button>

          {/* Move Down */}
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={onMoveDown}
            disabled={index === totalBlocks - 1}
            title="Move block down"
            className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
          >
            <ChevronDown className="w-4 h-4" />
          </Button>

          {/* Delete */}
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={onRemove}
            title="Delete block"
            className="text-red-500 hover:text-red-700"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Enabled Checkbox Controller */}
      <Controller
        name={`blocks.${index}.enabled`}
        control={control}
        render={({ field }) => (
          <input
            {...field}
            type="hidden"
            value={field.value ? 'true' : 'false'}
          />
        )}
      />

      {/* Block Form - Only show fields if enabled or show dimmed if disabled */}
      <div className={enabled ? '' : 'opacity-60 pointer-events-none'}>
        <Controller
          name={`blocks.${index}.rule_type`}
          control={control}
          render={({ field }) => (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rule Type *
              </label>
              <select
                value={field.value || ''}
                onChange={(e) => field.onChange(e.target.value)}
                disabled={!enabled}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select rule type</option>
                <option value="hourly">Hourly Rate</option>
                <option value="fixed">Fixed Fee</option>
                <option value="retainer">Retainer</option>
                <option value="session-based">Session-Based</option>
                <option value="per-item">Per Item</option>
                <option value="tiered">Tiered Pricing</option>
                <option value="event-based">Event-Based</option>
                <option value="travel">Travel Fees</option>
              </select>
              {blockErrors.rule_type?.message && (
                <p className="text-sm text-red-600 mt-1">{blockErrors.rule_type.message}</p>
              )}
            </div>
          )}
        />

        {field.rule_type && (
          <DynamicBillingRuleForm
            ruleType={field.rule_type as RuleType}
            control={control}
            errors={blockErrors}
            disabled={!enabled}
            showTypeDescription={false}
            fieldPrefix={`blocks.${index}.`}
          />
        )}
      </div>
    </div>
  );
};

export default BillingRuleBlock;
