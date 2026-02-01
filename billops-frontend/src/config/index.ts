/**
 * Environment configuration
 * Provides type-safe access to environment variables
 */

interface Config {
  apiUrl: string;
  apiTimeout: number;
  appName: string;
  appVersion: string;
  enableAnalytics: boolean;
  enableDebug: boolean;
  isDev: boolean;
  isProd: boolean;
}

const config: Config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10),
  appName: import.meta.env.VITE_APP_NAME || 'BillOps',
  appVersion: import.meta.env.VITE_APP_VERSION || '0.1.0',
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  enableDebug: import.meta.env.VITE_ENABLE_DEBUG === 'true',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
};

export default config;
