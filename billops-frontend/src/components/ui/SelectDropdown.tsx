/**
 * Reusable Select Dropdown component for forms
 */

import clsx from 'clsx';

export interface SelectOption {
  label: string;
  value: string;
}

interface SelectDropdownProps {
  value: string | undefined;
  onChange: (value: string) => void;
  options: SelectOption[];
  label?: string;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  allowEmpty?: boolean;
}

export const SelectDropdown = ({
  value,
  onChange,
  options,
  label,
  placeholder,
  error,
  disabled = false,
  allowEmpty = false,
}: SelectDropdownProps) => {
  return (
    <div>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={clsx(
          'w-full px-3 py-2 rounded-lg border transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-blue-500',
          error
            ? 'border-red-300 bg-red-50'
            : 'border-gray-300 bg-white hover:border-gray-400'
        )}
      >
        {allowEmpty || !value ? (
          <option value="">{placeholder || 'Select an option'}</option>
        ) : null}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};
