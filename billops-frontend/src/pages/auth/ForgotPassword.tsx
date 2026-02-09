/**
 * Forgot Password Page
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '@/components/layouts/AuthLayout';
import { FormInput } from '@/components/forms/FormInput';
import { FormError } from '@/components/forms/FormError';
import { FormSuccess } from '@/components/forms/FormSuccess';
import { useAuth } from '@/context/AuthContext';
import { forgotPasswordSchema, ForgotPasswordFormData } from '@/schemas/auth';

export default function ForgotPassword() {
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const { forgotPassword, isLoading, error, clearError } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  // Clear error on component unmount
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  const onSubmit = async (data: ForgotPasswordFormData) => {
    try {
      await forgotPassword(data);
      setSuccessMessage('Password reset link has been sent to your email. Check your inbox!');
      reset();
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch {
      // Error is handled by useAuth hook
    }
  };

  return (
    <AuthLayout
      title="Reset Password"
      subtitle="Enter your email to receive a password reset link"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <FormError message={error} />
        <FormSuccess message={successMessage} />

        <FormInput
          label="Email Address"
          type="email"
          placeholder="you@example.com"
          {...register('email')}
          error={errors.email?.message}
        />

        <button
          type="submit"
          disabled={isLoading || !!successMessage}
          className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Sending link...' : 'Send Reset Link'}
        </button>
      </form>

      <div className="space-y-4 pt-4 border-t border-gray-200">
        <div className="text-center text-sm text-gray-600">
          Remember your password?{' '}
          <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
            Back to login
          </Link>
        </div>

        <div className="text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/signup" className="text-blue-600 hover:text-blue-700 font-medium">
            Sign up
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
}
