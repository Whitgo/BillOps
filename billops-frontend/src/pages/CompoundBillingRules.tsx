/**
 * Compound Billing Rules Page
 * Demonstrates the multi-block billing rule system with reordering, enabling/disabling, and deletion
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal, Button, Input } from '@/components/ui';
import { SelectDropdown } from '@/components/ui/SelectDropdown';
import BillingRuleBlocksManager from '@/components/forms/BillingRuleBlocksManager';
import { Plus, Trash2, Edit2 } from 'lucide-react';
import clsx from 'clsx';
import { compoundBillingRuleSchema, type CompoundBillingRuleFormData } from '@/schemas/compoundBillingRule';
import { useProjects } from '@/services/queries/hooks';

export default function CompoundBillingRules() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [compoundRules] = useState<any[]>([]); // Placeholder for fetched rules
  
  const { data: projectsData } = useProjects(0, 100);

  const form = useForm<CompoundBillingRuleFormData>({
    resolver: zodResolver(compoundBillingRuleSchema),
    defaultValues: {
      project_id: '',
      blocks: [
        {
          block_id: 'block_1',
          rule_type: 'fixed',
          rate_cents: 50000,
          currency: 'USD',
          enabled: true,
          order: 0,
        },
      ],
    },
  });

  const handleCreate = () => {
    form.reset({
      project_id: '',
      blocks: [
        {
          block_id: `block_${Date.now()}`,
          rule_type: 'hourly',
          rate_cents: 0,
          currency: 'USD',
          enabled: true,
          order: 0,
        },
      ],
    });
    setIsModalOpen(true);
  };

  const onSubmit = async (data: CompoundBillingRuleFormData) => {
    console.log('Compound billing rule data:', data);
    setIsModalOpen(false);
    // TODO: Call API to save compound billing rule
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compound Billing Rules</h1>
          <p className="mt-1 text-gray-600">
            Create complex billing strategies by combining multiple rule blocks
          </p>
        </div>
        <Button onClick={handleCreate} disabled={false}>
          <Plus className="w-4 h-4 mr-2" />
          Create Compound Rule
        </Button>
      </div>

      {/* Info Banner */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4">
        <p className="text-sm text-purple-900">
          <strong>Compound Billing Rules:</strong> Combine multiple billing rule types to create sophisticated pricing models.
          Example: $500 fixed fee + $50 per revision + 20% project deposit.
        </p>
      </div>

      {/* Empty State */}
      {compoundRules.length === 0 && (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6m0 0v6m0-6h6m0 0h6m0 0v6m0-6h-6m0 0H6m0 0v-6m0 6h6" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No compound billing rules yet</h3>
          <p className="text-sm text-gray-500 mb-4">Start creating sophisticated billing strategies</p>
          <Button onClick={handleCreate}>
            <Plus className="w-4 h-4 mr-2" />
            Create Your First Rule
          </Button>
        </div>
      )}

      {/* Compound Rules List - Would show saved rules here */}
      {compoundRules.length > 0 && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Project</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Blocks</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {/* Placeholder for rule rows */}
            </tbody>
          </table>
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          form.reset();
        }}
        title="Create Compound Billing Rule"
        size="2xl"
      >
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Project Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Project *
            </label>
            <SelectDropdown
              label=""
              value={form.watch('project_id')}
              onChange={(val) => form.setValue('project_id', val)}
              options={[
                { label: 'Select a project', value: '' },
                ...(projectsData?.items || []).map((p) => ({
                  label: p.name,
                  value: p.id,
                })),
              ]}
            />
            {form.formState.errors.project_id && (
              <p className="text-sm text-red-600 mt-1">
                {form.formState.errors.project_id.message}
              </p>
            )}
          </div>

          {/* Blocks Manager */}
          <BillingRuleBlocksManager
            control={form.control}
            errors={form.formState.errors}
          />

          {/* Submit Buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              type="submit"
              className="flex-1"
            >
              Create Compound Rule
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsModalOpen(false);
                form.reset();
              }}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>

      {/* Usage Examples */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Example 1: Project-Based Billing</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">1.</span>
              <span>$5,000 Fixed fee (project setup)</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">2.</span>
              <span>$150/hour for development time</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">3.</span>
              <span>$50 per revision after launch</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Example 2: Retainer + Travel</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex items-start gap-2">
              <span className="text-green-600 font-bold">1.</span>
              <span>$3,000/month retainer (20 hours included)</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-green-600 font-bold">2.</span>
              <span>$125/hour overtime (1.5x multiplier)</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-green-600 font-bold">3.</span>
              <span>$0.65/mile travel + parking pass-through</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
