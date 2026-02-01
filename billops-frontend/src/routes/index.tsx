/**
 * React Router configuration and routes
 */

import { createBrowserRouter, RouteObject } from 'react-router-dom';
import MainLayout from '@/components/layouts/MainLayout';

// Page imports - will be expanded as features are built
import Home from '@/pages/Home';
import NotFound from '@/pages/NotFound';

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <MainLayout />,
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
