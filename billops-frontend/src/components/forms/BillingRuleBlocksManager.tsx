/**
 * Billing Rule Blocks Manager Component
 * Manages multiple billing rule blocks with reordering, enabling/disabling, and deletion
 */

import React from 'react';
import { useFieldArray, Control, Controller } from 'react-hook-form';
import { Plus } from 'lucide-react';
import BillingRuleBlock from './BillingRuleBlock';
import { Button, Input } from '@/components/ui';
import type { CompoundBillingRuleFormData } from '@/schemas/compoundBillingRule';
import clsx from 'clsx';

interface BillingRuleBlocksManagerProps {
  control: Control<CompoundBillingRuleFormData>;
  errors?: Record<string, any>;
}

/**
 * Generates a unique ID for a rule block
 */
const generateBlockId = (): string => `block_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export const BillingRuleBlocksManager: React.FC<BillingRuleBlocksManagerProps> = ({
  control,
  errors = {},
}) => {
  const { fields, append, remove, move } = useFieldArray({
    control,
    name: 'blocks',
  });

  const handleAddBlock = () => {
    append({
      block_id: generateBlockId(),
      rule_type: 'hourly',
      rate_cents: 0,
      currency: 'USD',
      enabled: true,
      order: fields.length,
      effective_from: '',
      effective_to: '',
    } as any);
  };

  const handleMoveBlock = (fromIndex: number, direction: 'up' | 'down') => {
    if (direction === 'up' && fromIndex > 0) {
      move(fromIndex, fromIndex - 1);
    } else if (direction === 'down' && fromIndex < fields.length - 1) {
      move(fromIndex, fromIndex + 1);
    }
  };

  const handleToggleBlock = (index: number) => {
    const field = fields[index];
    // Toggle the enabled state
    control._formValues.blocks[index] = {
      ...field,
      enabled: !field.enabled,
    };
  };

  return (
    <div className="space-y-4">
      {/* Info Section */}
      <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
        <p className="text-sm text-amber-900">
          <strong>Compound Billing Rules:</strong> Add multiple billing rule blocks to create complex pricing strategies.
          For example: $500 fixed fee + $50 per revision + 20% deposit.
        </p>
      </div>

      {/* Blocks List */}
      {fields.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
          <p className="text-gray-600 mb-4">No billing rule blocks yet</p>
          <Button
            type="button"
            onClick={handleAddBlock}
            className="inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add First Block
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {fields.map((field, index) => (
            <BillingRuleBlock
              key={field.id}
              field={field}
              index={index}
              totalBlocks={fields.length}
              control={control}
              errors={errors}
              onRemove={() => remove(index)}
              onMoveUp={() => handleMoveBlock(index, 'up')}
              onMoveDown={() => handleMoveBlock(index, 'down')}
              onToggle={() => handleToggleBlock(index)}
            />
          ))}
        </div>
      )}

      {/* Add Block Button */}
      <Button
        type="button"
        variant="outline"
        onClick={handleAddBlock}
        className="w-full"
      >
        <Plus className="w-4 h-4 mr-2" />
        Add Another Block
      </Button>

      {/* Summary */}
      {fields.length > 0 && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
          <p className="text-sm font-medium text-blue-900 mb-2">Rule Summary:</p>
          <div className="space-y-1">
            {fields
              .filter((field) => field.enabled !== false)
              .map((field, index) => (
                <div key={field.id} className="text-sm text-blue-800 flex items-start gap-2">
                  <span className="font-medium">{index + 1}.</span>
                  <div>
                    <div className="font-mono font-semibold">
                      {`$${(field.rate_cents ? field.rate_cents / 100 : 0).toFixed(2)} - ${field.rule_type}`}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Global Effective Dates */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3">
        <p className="text-sm font-medium text-gray-900">Effective Period (applies to all blocks)</p>
        <div className="grid grid-cols-2 gap-3">
          <Controller
            name="effective_from"
            control={control}
            render={({ field }) => (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Effective From
                </label>
                <input
                  {...field}
                  type="date"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Start date"
                />
              </div>
            )}
          />
          <Controller
            name="effective_to"
            control={control}
            render={({ field }) => (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Effective To (Optional)
                </label>
                <input
                  {...field}
                  type="date"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="End date"
                />
              </div>
            )}
          />
        </div>
      </div>

      {/* Error Summary */}
      {errors && Object.keys(errors).length > 0 && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3">
          <p className="text-sm font-medium text-red-900 mb-2">Please fix the following errors:</p>
          <ul className="text-sm text-red-800 space-y-1">
            {Object.entries(errors).map(([key, value]: [string, any]) => (
              <li key={key} className="flex gap-2">
                <span>•</span>
                <span>{value?.message || `Error in ${key}`}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default BillingRuleBlocksManager;
