/**
 * React Router configuration and routes
 */
import { createBrowserRouter, RouteObject } from 'react-router-dom';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

// Auth page imports
import Login from '@/pages/auth/Login';
import Signup from '@/pages/auth/Signup';
import ForgotPassword from '@/pages/auth/ForgotPassword';
import ResetPassword from '@/pages/auth/ResetPassword';

// Page imports - will be expanded as features are built
import Home from '@/pages/Home';
import NotFound from '@/pages/NotFound';

export const routes: RouteObject[] = [
  // Auth Routes (not protected)
  {
    path: 'login',
    element: <Login />,
  },
  {
    path: 'signup',
    element: <Signup />,
  },
  {
    path: 'forgot-password',
    element: <ForgotPassword />,
  },
  {
    path: 'reset-password',
    element: <ResetPassword />,
  },

  // Main Routes (protected)
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: 'dashboard',
        lazy: () => import('@/pages/Dashboard').then(m => ({ Component: m.default })),
      },
      {
        path: 'clients',
        lazy: () => import('@/pages/Clients').then(m => ({ Component: m.default })),
      },
      {
        path: 'projects',
        lazy: () => import('@/pages/Projects').then(m => ({ Component: m.default })),
      },
      {
        path: 'invoices',
        lazy: () => import('@/pages/Invoices').then(m => ({ Component: m.default })),
      },
      {
        path: 'invoices/:id',
        lazy: () => import('@/pages/InvoiceDetail').then(m => ({ Component: m.default })),
      },
      {
        path: 'time-capture',
        lazy: () => import('@/pages/TimeCapture').then(m => ({ Component: m.default })),
      },
      {
        path: 'billing-rules',
        lazy: () => import('@/pages/BillingRules').then(m => ({ Component: m.default })),
      },
      {
        path: 'users',
        lazy: () => import('@/pages/Users').then(m => ({ Component: m.default })),
      },
      {
        path: 'settings',
        lazy: () => import('@/pages/Settings').then(m => ({ Component: m.default })),
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
];
export const router = createBrowserRouter(routes);
