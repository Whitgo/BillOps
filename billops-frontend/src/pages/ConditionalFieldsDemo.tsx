/**
 * Example page demonstrating conditional billing rule fields
 * Shows practical examples of how advanced fields are used
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal, Button } from '@/components/ui';
import { DynamicBillingRuleForm } from '@/components/forms/DynamicBillingRuleForm';
import { billingRuleFormSchema, type BillingRuleFormData } from '@/schemas/billingRule';
import type { RuleType } from '@/config/billingRuleConfig';
import { Plus } from 'lucide-react';

export default function ConditionalFieldsDemo() {
  const [selectedRuleType, setSelectedRuleType] = useState<RuleType>('fixed');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const form = useForm<BillingRuleFormData>({
    resolver: zodResolver(billingRuleFormSchema),
    defaultValues: {
      project_id: '',
      rule_type: 'fixed',
      rate_cents: 0,
      currency: 'USD',
    },
  });

  const onSubmit = (data: BillingRuleFormData) => {
    console.log('Form data:', data);
    alert('Form submitted! Check console for data. Note: is_art_commission, revisions_included, etc. are included even if unchecked.');
  };

  const examples = [
    {
      type: 'fixed' as RuleType,
      title: 'Art Commission',
      description: 'Fixed fee project with revision tracking and deposit requirements',
      fields: ['$500 base fee', 'Enable "Art Commission Project"', '2 revisions included', '20% deposit required', 'Balance on delivery'],
    },
    {
      type: 'per-item' as RuleType,
      title: 'Notary Service',
      description: 'Per-document notary fees with stamp surcharges and rush options',
      fields: ['$25 per document', 'Enable "Notary Service"', '$5 per stamp', '$10 remote notary premium', 'Rush processing available'],
    },
    {
      type: 'hourly' as RuleType,
      title: 'Specialist Developer',
      description: 'Hourly with specialization rates for complex work',
      fields: ['$150/hour base', 'Enable "Specialization Rates"', '1.5x multiplier for complex work', '$100 emergency fee', '2-hour minimum'],
    },
    {
      type: 'retainer' as RuleType,
      title: 'Premium Support',
      description: 'Retainer with tiered SLA and priority support',
      fields: ['$3000/month retainer', '160 hours included', 'Enable "Support Tier Pricing"', '2-hour SLA response', '$500/month priority upgrade'],
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Conditional Billing Fields</h1>
        <p className="text-gray-600 text-lg">
          Advanced fields appear dynamically based on your needs. Only relevant configuration options are shown.
        </p>
      </div>

      {/* Examples Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {examples.map((example) => (
          <div
            key={example.type}
            className="bg-white border-2 border-gray-200 rounded-lg p-6 hover:border-blue-400 transition-colors cursor-pointer"
            onClick={() => {
              setSelectedRuleType(example.type);
              setIsModalOpen(true);
            }}
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{example.title}</h3>
            <p className="text-sm text-gray-600 mb-4">{example.description}</p>
            <div className="space-y-1">
              {example.fields.map((field, idx) => (
                <div key={idx} className="text-xs text-gray-600 flex items-start gap-2">
                  <span className="text-blue-500 font-bold">•</span>
                  <span>{field}</span>
                </div>
              ))}
            </div>
            <Button className="w-full mt-4" size="sm">
              Try This Example
            </Button>
          </div>
        ))}
      </div>

      {/* Information Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-4">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h3 className="font-medium text-blue-900 mb-2">1. Select Rule Type</h3>
            <p className="text-sm text-blue-800">Choose the billing model that matches your business (Fixed, Hourly, Retainer, etc.)</p>
          </div>
          <div>
            <h3 className="font-medium text-blue-900 mb-2">2. Configure Base Fields</h3>
            <p className="text-sm text-blue-800">Enter essential information like rate, currency, and description</p>
          </div>
          <div>
            <h3 className="font-medium text-blue-900 mb-2">3. Enable Advanced Options</h3>
            <p className="text-sm text-blue-800">Scroll to Advanced Options and enable toggles for relevant features</p>
          </div>
        </div>
      </div>

      {/* Detailed Examples */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Detailed Examples</h2>

        {/* Art Commission Example */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Example 1: Art Commission (Fixed Fee)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-3">When you enable "Art Commission Project":</p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Revisions Included"</strong> appears - specify how many free revision rounds</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Per-Revision Fee"</strong> appears - charge for revisions beyond included</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Deposit Percentage"</strong> appears - require upfront payment (e.g., 20%)</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Payment Schedule"</strong> appears - define milestone payments</span>
                </li>
              </ul>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded p-4">
              <p className="text-sm font-medium text-amber-900 mb-2">Preview Result:</p>
              <div className="bg-white p-3 rounded border border-amber-200">
                <p className="text-base font-mono text-amber-900">
                  $500 + 2 revisions, 20% deposit
                </p>
              </div>
              <p className="text-xs text-amber-700 mt-3">
                The form data includes all fields including disabled ones, allowing flexible billing scenarios.
              </p>
            </div>
          </div>
        </div>

        {/* Notary Service Example */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Example 2: Notary Service (Per Item)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-3">When you enable "Notary Service":</p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Per Stamp Fee"</strong> appears - charge extra per notary seal</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Travel Fee Included"</strong> appears - toggle if travel is separate</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Remote Notary Premium"</strong> appears - extra charge for online</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Rush Processing"</strong> appears - enable expedited services</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-green-600">✓</span>
                  <span><strong>"Certification Type"</strong> appears - jurat, acknowledged, etc.</span>
                </li>
              </ul>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded p-4">
              <p className="text-sm font-medium text-amber-900 mb-2">Preview Result:</p>
              <div className="bg-white p-3 rounded border border-amber-200">
                <p className="text-base font-mono text-amber-900">
                  $25 per document<br/>
                  (+$5/stamp, +$10 remote)
                </p>
              </div>
              <p className="text-xs text-amber-700 mt-3">
                All relevant billing components are captured for accurate invoicing.
              </p>
            </div>
          </div>
        </div>

        {/* Complex Dependency Example */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Example 3: Cascading Dependencies (Retainer)</h3>
          <div className="bg-gray-50 rounded p-4 text-sm font-mono space-y-2">
            <p><span className="text-blue-600">Base Fields:</span> Monthly rate, included hours, overtime multiplier</p>
            <p><span className="text-blue-600">Advanced Toggle:</span> ☐ Support Tier Pricing</p>
            <p className="ml-4 text-gray-600">When UNCHECKED: These fields hidden:</p>
            <ul className="ml-8 text-gray-600 space-y-1">
              <li>• Response Time SLA</li>
              <li>• Priority Support Fee</li>
              <li>• Monthly Consultation</li>
            </ul>
            <p className="ml-4 text-gray-600 mt-2">When CHECKED: These fields appear:</p>
            <ul className="ml-8 text-green-700 space-y-1">
              <li>✓ Response Time SLA (required)</li>
              <li>✓ Priority Support Fee (optional)</li>
              <li>✓ Monthly Consultation (checkbox)</li>
              <li>✓ Minimum Contract Months</li>
              <li>✓ Annual Prepay Discount %</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Key Benefits */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-green-900 mb-4">Key Benefits</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-green-900 mb-2">User Experience</h4>
            <ul className="text-sm text-green-800 space-y-1">
              <li>✓ Only relevant fields shown</li>
              <li>✓ Reduces form overwhelming</li>
              <li>✓ Clear contextual guidance</li>
              <li>✓ Logical field grouping</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-green-900 mb-2">Business Flexibility</h4>
            <ul className="text-sm text-green-800 space-y-1">
              <li>✓ Support complex pricing models</li>
              <li>✓ Industry-specific configurations</li>
              <li>✓ Adaptable to any service type</li>
              <li>✓ Easy to add new scenarios</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Demo Button */}
      <div className="flex justify-center">
        <Button
          onClick={() => {
            setSelectedRuleType('fixed');
            setIsModalOpen(true);
          }}
          size="lg"
          className="inline-flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Try Interactive Demo
        </Button>
      </div>

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Configure ${selectedRuleType.charAt(0).toUpperCase() + selectedRuleType.slice(1)} Rule`}
        size="lg"
      >
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <DynamicBillingRuleForm
            ruleType={selectedRuleType}
            control={form.control}
            errors={form.formState.errors}
            showTypeDescription
          />

          <div className="flex gap-3 pt-4 border-t">
            <Button type="submit" className="flex-1">
              Save Rule
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsModalOpen(false)}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
