/**
 * Reset Password Page
 */

import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '@/components/layouts/AuthLayout';
import { FormInput } from '@/components/forms/FormInput';
import { FormError } from '@/components/forms/FormError';
import { FormSuccess } from '@/components/forms/FormSuccess';
import { useAuth } from '@/context/AuthContext';
import { resetPasswordSchema, ResetPasswordFormData } from '@/schemas/auth';

export default function ResetPassword() {
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { resetPassword, isLoading, error, clearError } = useAuth();

  const token = searchParams.get('token') || '';

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  const onSubmit = async (data: ResetPasswordFormData) => {
    try {
      await resetPassword({
        token,
        password: data.password,
        confirmPassword: data.confirmPassword,
      });
      setSuccessMessage('Password reset successful! Redirecting to login...');
      reset();
      setTimeout(() => navigate('/login'), 2000);
    } catch {
      // Error handled by useAuth
    }
  };

  if (!token) {
    return (
      <AuthLayout title="Invalid Reset Link" subtitle="The reset link is missing or invalid">
        <div className="space-y-4">
          <FormError message="Missing reset token. Please request a new reset link." />
          <Link to="/forgot-password" className="btn btn-primary w-full">
            Request New Link
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Set New Password" subtitle="Create a strong new password">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <FormError message={error} />
        <FormSuccess message={successMessage} />

        <FormInput
          label="New Password"
          type="password"
          placeholder="••••••••"
          {...register('password')}
          error={errors.password?.message}
          helperText="At least 8 characters with uppercase, lowercase, number, and special character"
        />

        <FormInput
          label="Confirm Password"
          type="password"
          placeholder="••••••••"
          {...register('confirmPassword')}
          error={errors.confirmPassword?.message}
        />

        <button
          type="submit"
          disabled={isLoading || !!successMessage}
          className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Resetting...' : 'Reset Password'}
        </button>
      </form>

      <div className="text-center text-sm text-gray-600 pt-4 border-t border-gray-200">
        Remember your password?{' '}
        <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
          Back to login
        </Link>
      </div>
    </AuthLayout>
  );
}
