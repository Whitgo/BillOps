/**
 * Billing Rules Page - Configuration-Driven Dynamic Forms
 * Supports: hourly, fixed, retainer, session-based, per-item, tiered, event-based, travel
 */

import { useState, useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal, Button, Input } from '@/components/ui';
import { SelectDropdown } from '@/components/ui/SelectDropdown';
import { DynamicBillingRuleForm } from '@/components/forms/DynamicBillingRuleForm';
import {
  useBillingRules,
  useCreateBillingRule,
  useUpdateBillingRule,
  useDeleteBillingRule,
} from '@/services/queries/hooks';
import { useProjects } from '@/services/queries/hooks';
import { billingRuleFormSchema, type BillingRuleFormData } from '@/schemas/billingRule';
import type { BillingRule } from '@/types/billingRule';
import type { RuleType } from '@/config/billingRuleConfig';
import {
  getRuleTypeOptions,
  generateRulePreview,
  getRuleTypeBadge,
} from '@/config/billingRuleConfig';
import {
  getBillingRuleTemplate,
  getBillingRuleTemplateOptions,
} from '@/config/billingRuleTemplates';
import { Plus, Trash2, Edit2, DollarSign, Calendar } from 'lucide-react';
import clsx from 'clsx';

const PAGE_SIZE = 10;

const badgeColorMap: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-800',
  purple: 'bg-purple-100 text-purple-800',
  green: 'bg-green-100 text-green-800',
  orange: 'bg-orange-100 text-orange-800',
  red: 'bg-red-100 text-red-800',
  indigo: 'bg-indigo-100 text-indigo-800',
  pink: 'bg-pink-100 text-pink-800',
};

export default function BillingRules() {
  const [page, setPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<BillingRule | null>(null);
  const [projectFilter, setProjectFilter] = useState<string>('');
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');

  // Fetch billing rules
  const { data: rulesData, isLoading: rulesLoading } = useBillingRules(
    (page - 1) * PAGE_SIZE,
    PAGE_SIZE,
    projectFilter || undefined
  );

  // Fetch projects for dropdown
  const { data: projectsData } = useProjects(0, 100);

  // Mutations
  const createRule = useCreateBillingRule();
  const updateRule = useUpdateBillingRule();
  const deleteRule = useDeleteBillingRule();

  // Form
  const form = useForm<BillingRuleFormData>({
    resolver: zodResolver(billingRuleFormSchema),
    defaultValues: {
      project_id: '',
      rule_type: 'hourly',
      rate_cents: 10000,
      currency: 'USD',
      effective_from: new Date().toISOString().slice(0, 10),
      effective_to: '',
    },
  });

  const rules = rulesData?.items || [];
  const total = rulesData?.total || 0;
  const selectedRuleType = form.watch('rule_type') as RuleType;

  // Map for project lookup
  const projectMap = useMemo(
    () =>
      new Map(
        (projectsData?.items || []).map((p) => [p.id, p])
      ),
    [projectsData]
  );

  // Reset form
  const resetForm = () => {
    form.reset({
      project_id: '',
      rule_type: 'hourly',
      rate_cents: 10000,
      currency: 'USD',
      effective_from: new Date().toISOString().slice(0, 10),
      effective_to: '',
    });
    setSelectedRule(null);
    setSelectedTemplateId('');
  };

  const emptyTemplateValues: Partial<BillingRuleFormData> = {
    rounding_increment_minutes: undefined,
    overtime_multiplier: undefined,
    cap_hours: undefined,
    retainer_hours: undefined,
    session_max_duration: undefined,
    item_description: undefined,
    tier1_threshold: undefined,
    tier1_rate_cents: undefined,
    tier2_threshold: undefined,
    tier2_rate_cents: undefined,
    tier3_rate_cents: undefined,
    event_types: undefined,
    rate_per_event_cents: undefined,
    hourly_rate_cents: undefined,
    mileage_rate_cents: undefined,
    parking_charges: undefined,
    meta: undefined,
  };

  const applyTemplate = (templateId: string) => {
    const template = getBillingRuleTemplate(templateId);
    if (!template) return;

    const currentValues = form.getValues();
    const today = new Date().toISOString().slice(0, 10);

    form.reset({
      ...currentValues,
      ...emptyTemplateValues,
      rule_type: template.ruleType,
      rate_cents: template.defaults.rate_cents ?? currentValues.rate_cents ?? 0,
      currency: template.defaults.currency ?? currentValues.currency ?? 'USD',
      effective_from: currentValues.effective_from || today,
      effective_to: '',
      ...template.defaults,
    });
  };

  // Open create modal
  const handleCreate = () => {
    resetForm();
    setIsModalOpen(true);
  };

  const isNumber = (value: unknown): value is number =>
    typeof value === 'number' && !Number.isNaN(value);

  const isString = (value: unknown): value is string => typeof value === 'string';

  const isStringArray = (value: unknown): value is string[] =>
    Array.isArray(value) && value.every((item) => typeof item === 'string');

  const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean';

  // Open edit modal
  const handleEdit = (rule: BillingRule) => {
    setSelectedRule(rule);
    setSelectedTemplateId('');
    const meta = rule.meta ?? {};
    const resetValues: BillingRuleFormData = {
      project_id: rule.project_id,
      rule_type: rule.rule_type,
      rate_cents: rule.rate_cents,
      currency: rule.currency,
      // Hourly rule fields
      rounding_increment_minutes: rule.rounding_increment_minutes,
      overtime_multiplier: rule.overtime_multiplier,
      cap_hours: rule.cap_hours,
      // Retainer rule fields
      retainer_hours: rule.retainer_hours,
      // Session-based
      session_max_duration: isNumber(meta.session_max_duration)
        ? meta.session_max_duration
        : undefined,
      // Per-item
      item_description: isString(meta.item_description) ? meta.item_description : undefined,
      // Tiered
      tier1_threshold: isNumber(meta.tier1_threshold) ? meta.tier1_threshold : undefined,
      tier1_rate_cents: isNumber(meta.tier1_rate_cents) ? meta.tier1_rate_cents : undefined,
      tier2_threshold: isNumber(meta.tier2_threshold) ? meta.tier2_threshold : undefined,
      tier2_rate_cents: isNumber(meta.tier2_rate_cents) ? meta.tier2_rate_cents : undefined,
      tier3_rate_cents: isNumber(meta.tier3_rate_cents) ? meta.tier3_rate_cents : undefined,
      // Event-based
      event_types: isStringArray(meta.event_types) ? meta.event_types : undefined,
      rate_per_event_cents: isNumber(meta.rate_per_event_cents)
        ? meta.rate_per_event_cents
        : undefined,
      // Travel
      hourly_rate_cents: isNumber(meta.hourly_rate_cents) ? meta.hourly_rate_cents : undefined,
      mileage_rate_cents: isNumber(meta.mileage_rate_cents) ? meta.mileage_rate_cents : undefined,
      parking_charges: isBoolean(meta.parking_charges) ? meta.parking_charges : undefined,
      meta: rule.meta,
      effective_from: rule.effective_from ? rule.effective_from.slice(0, 10) : '',
      effective_to: rule.effective_to ? rule.effective_to.slice(0, 10) : '',
    };
    form.reset(resetValues);
    setIsModalOpen(true);
  };

  // Submit handler
  const onSubmit = async (data: BillingRuleFormData) => {
    try {
      if (selectedRule) {
        await updateRule.mutateAsync({
          id: selectedRule.id,
          data,
        });
      } else {
        await createRule.mutateAsync(data);
      }
      setIsModalOpen(false);
      resetForm();
    } catch (error) {
      console.error('Failed to save billing rule:', error);
    }
  };

  // Delete handler
  const handleDelete = async () => {
    if (!selectedRule) return;
    try {
      await deleteRule.mutateAsync(selectedRule.id);
      setIsDeleteOpen(false);
      setSelectedRule(null);
    } catch (error) {
      console.error('Failed to delete billing rule:', error);
    }
  };

  // Format currency for display
  const formatCurrency = (cents: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(cents / 100);
  };

  // Check if rule is active
  const isRuleActive = (rule: BillingRule) => {
    const now = new Date();
    const start = new Date(rule.effective_from);
    const end = rule.effective_to ? new Date(rule.effective_to) : null;
    return start <= now && (!end || end > now);
  };

  // Get badge styling
  const getBadgeClass = (ruleType: RuleType) => {
    const badge = getRuleTypeBadge(ruleType);
    return badgeColorMap[badge.color];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Billing Rules</h1>
          <p className="mt-1 text-gray-600">
            Configure billing logic using a flexible, rule-based system
          </p>
        </div>
        <Button onClick={handleCreate} disabled={createRule.isPending}>
          <Plus className="w-4 h-4 mr-2" />
          Add Rule
        </Button>
      </div>

      {/* Info Banner */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>Supported Rule Types:</strong> Hourly, Fixed Fee, Retainer, Session-Based, Per-Item, Tiered Pricing, Event-Based, and Travel Fees. Each rule type has custom fields optimized for different billing scenarios.
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-4">
        <SelectDropdown
          label="Filter by Project"
          value={projectFilter}
          onChange={setProjectFilter}
          options={[
            { label: 'All Projects', value: '' },
            ...(projectsData?.items || []).map((p) => ({
              label: p.name,
              value: p.id,
            })),
          ]}
          allowEmpty
        />
      </div>

      {/* Rules List */}
      <div className="bg-white shadow rounded-lg">
        {rulesLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin">
              <DollarSign className="w-8 h-8 text-gray-400" />
            </div>
          </div>
        ) : rules.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <DollarSign className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-gray-600 font-medium">No billing rules yet</p>
              <p className="text-sm text-gray-500 mt-1">Click "Add Rule" to create your first rule</p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Project
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Configuration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Effective Period
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {rules.map((rule: BillingRule) => {
                  const project = projectMap.get(rule.project_id);
                  const active = isRuleActive(rule);
                  const badge = getRuleTypeBadge(rule.rule_type as RuleType);
                  const preview = generateRulePreview(rule.rule_type as RuleType, {
                    ...rule,
                    ...(rule.meta || {}),
                  });

                  return (
                    <tr key={rule.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">
                          {project?.name || 'Unknown Project'}
                        </span>
                        <p className="text-xs text-gray-500">{project?.id}</p>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={clsx('inline-block px-3 py-1 rounded-full text-xs font-semibold', getBadgeClass(rule.rule_type as RuleType))}>
                          {badge.text}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">{preview}</div>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatCurrency(rule.rate_cents, rule.currency)} base rate
                        </p>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={clsx(
                          'inline-block px-2 py-1 rounded text-xs font-medium',
                          active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-700'
                        )}>
                          {active ? '✓ Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        <div className="flex items-start gap-1">
                          <Calendar className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
                          <div>
                            <p>{new Date(rule.effective_from).toLocaleDateString()}</p>
                            {rule.effective_to && (
                              <p className="text-xs">{new Date(rule.effective_to).toLocaleDateString()}</p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(rule)}
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => {
                              setSelectedRule(rule);
                              setIsDeleteOpen(true);
                            }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {total > PAGE_SIZE && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {(page - 1) * PAGE_SIZE + 1} to {Math.min(page * PAGE_SIZE, total)} of{' '}
              {total} rules
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page * PAGE_SIZE >= total}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          resetForm();
        }}
        title={selectedRule ? 'Edit Billing Rule' : 'Create Billing Rule'}
        size="lg"
      >
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-gray-900">Professional Templates</p>
                <p className="text-xs text-gray-600">
                  Start with a template to pre-fill the rule type and defaults.
                </p>
              </div>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={!selectedTemplateId}
                onClick={() => applyTemplate(selectedTemplateId)}
              >
                Apply Template
              </Button>
            </div>
            <SelectDropdown
              label="Template"
              value={selectedTemplateId}
              onChange={setSelectedTemplateId}
              options={getBillingRuleTemplateOptions()}
              placeholder="Choose a profession"
              allowEmpty
            />
            {selectedTemplateId && (
              <p className="text-xs text-gray-600">
                {getBillingRuleTemplate(selectedTemplateId)?.description}
              </p>
            )}
          </div>
          {/* Project Selection */}
          <Controller
            name="project_id"
            control={form.control}
            render={({ field: { value, onChange }, fieldState }) => (
              <SelectDropdown
                label="Project *"
                value={value}
                onChange={onChange}
                options={
                  projectsData?.items.map((p) => ({
                    label: p.name,
                    value: p.id,
                  })) || []
                }
                placeholder="Select a project"
                error={fieldState.error?.message}
              />
            )}
          />

          {/* Rule Type Selection */}
          <Controller
            name="rule_type"
            control={form.control}
            render={({ field: { value, onChange }, fieldState }) => (
              <SelectDropdown
                label="Rule Type *"
                value={value}
                onChange={onChange}
                options={getRuleTypeOptions()}
                error={fieldState.error?.message}
              />
            )}
          />

          {/* Dynamic Form based on Rule Type */}
          {selectedRuleType && (
            <DynamicBillingRuleForm
              ruleType={selectedRuleType}
              control={form.control}
              errors={form.formState.errors}
              showTypeDescription
            />
          )}

          {/* Effective Dates */}
          <div className="space-y-4 border-t pt-4">
            <h3 className="font-medium text-gray-900">Effective Period</h3>
            <Controller
              name="effective_from"
              control={form.control}
              render={({ field, fieldState }) => (
                <Input
                  {...field}
                  type="date"
                  label="Effective From *"
                  error={fieldState.error?.message}
                />
              )}
            />

            <Controller
              name="effective_to"
              control={form.control}
              render={({ field, fieldState }) => (
                <Input
                  {...field}
                  type="date"
                  label="Effective To (Optional)"
                  helperText="Leave blank for open-ended rules"
                  error={fieldState.error?.message}
                />
              )}
            />
          </div>

          {/* Preview */}
          {form.watch('rate_cents') > 0 && selectedRuleType && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm font-medium text-blue-900">Preview:</p>
              <p className="text-base font-semibold text-blue-800 mt-2">
                {generateRulePreview(selectedRuleType, form.getValues())}
              </p>
            </div>
          )}

          {/* Submit Buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              type="submit"
              disabled={createRule.isPending || updateRule.isPending}
              className="flex-1"
            >
              {selectedRule ? 'Save Changes' : 'Create Rule'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsModalOpen(false);
                resetForm();
              }}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Delete Billing Rule"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            Are you sure you want to delete this billing rule? This action cannot be undone.
          </p>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setIsDeleteOpen(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              variant="secondary"
              disabled={deleteRule.isPending}
              onClick={handleDelete}
              className="flex-1 text-red-600 hover:text-red-700"
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
