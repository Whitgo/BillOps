// API client placeholder. Update baseURL to point to your backend.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// Example helper for future fetch wrappers
export const withBase = (path: string) => `${API_BASE_URL}${path}`;
