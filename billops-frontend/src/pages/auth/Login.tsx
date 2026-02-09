/**
 * Login Page
 */

import { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '@/components/layouts/AuthLayout';
import { FormInput } from '@/components/forms/FormInput';
import { FormError } from '@/components/forms/FormError';
import { useAuth } from '@/context/AuthContext';
import { loginSchema, LoginFormData } from '@/schemas/auth';

export default function Login() {
  const navigate = useNavigate();
  const { login, isLoading, error, isAuthenticated, clearError } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
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

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data);
      navigate('/dashboard');
    } catch {
      // Error is handled by useAuth hook
    }
  };

  return (
    <AuthLayout title="Login" subtitle="Welcome back to BillOps">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <FormError message={error} />

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
        />

        <button
          type="submit"
          disabled={isLoading}
          className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>

      <div className="space-y-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <Link to="/forgot-password" className="text-sm text-blue-600 hover:text-blue-700">
            Forgot your password?
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
