/**
 * Custom hook for handling API errors
 */

import { useState } from 'react';
import { ApiError } from '@/types/api';

export function useApiError() {
  const [error, setError] = useState<ApiError | null>(null);

  const handleError = (err: unknown) => {
    const apiError = err instanceof Object && 'status' in err ? (err as ApiError) : null;
    setError(apiError || null);
  };

  const clearError = () => setError(null);

  return { error, handleError, clearError };
}
