/**
 * API module - centralized exports.
 *
 * This module re-exports the original api.ts for backward compatibility
 * while providing a modular structure for future development.
 */

// Re-export everything from the original api.ts for backward compatibility
export {
  api,
  AuthenticationError,
  setAuthErrorHandler,
} from '../api';

// Export all types
export * from './types';

// Export client utilities
export { ApiClient, apiClient } from './client';
