/**
 * Form Input component with error display
 */

import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

interface FormInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
}

export const FormInput = forwardRef<HTMLInputElement, FormInputProps>(
  ({ label, error, helperText, ...props }, ref) => {
    return (
      <div className="space-y-2">
        <label htmlFor={props.id} className="label">
          {label}
        </label>
        <input
          ref={ref}
          {...props}
          className={`input ${error ? 'border-red-500 focus:ring-red-500' : ''}`}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        {helperText && !error && <p className="text-sm text-gray-500">{helperText}</p>}
      </div>
    );
  }
);

FormInput.displayName = 'FormInput';
