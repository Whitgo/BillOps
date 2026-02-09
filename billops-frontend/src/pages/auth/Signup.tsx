/**
 * Signup Page
 */

import { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '@/components/layouts/AuthLayout';
import { FormInput } from '@/components/forms/FormInput';
import { FormError } from '@/components/forms/FormError';
import { useAuth } from '@/context/AuthContext';
import { signupSchema, SignupFormData } from '@/schemas/auth';

export default function Signup() {
  const navigate = useNavigate();
  const { signup, isLoading, error, isAuthenticated, clearError } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  // Clear error on component unmount
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  const onSubmit = async (data: SignupFormData) => {
    try {
      await signup(data);
      navigate('/dashboard');
    } catch {
      // Error is handled by useAuth hook
    }
  };

  return (
    <AuthLayout title="Create Account" subtitle="Join BillOps today">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <FormError message={error} />

        <FormInput
          label="Full Name"
          type="text"
          placeholder="John Doe"
          {...register('name')}
          error={errors.name?.message}
        />

        <FormInput
          label="Email"
          type="email"
          placeholder="you@example.com"
          {...register('email')}
          error={errors.email?.message}
        />

        <FormInput
          label="Password"
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
          disabled={isLoading}
          className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Creating account...' : 'Sign up'}
        </button>
      </form>

      <div className="text-center text-sm text-gray-600 pt-4 border-t border-gray-200">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
          Login
        </Link>
      </div>
    </AuthLayout>
  );
}
