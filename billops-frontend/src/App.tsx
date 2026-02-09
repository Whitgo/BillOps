/**
 * Main App Component
 * Sets up React Query and Router providers
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { queryClient } from '@/services/queries/client';
import { router } from '@/routes';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} fallbackElement={<PageSkeleton />} />
      </AuthProvider>
    </QueryClientProvider>
  );
}
