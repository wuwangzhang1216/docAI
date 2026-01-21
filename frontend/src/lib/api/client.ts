/**
 * API client base class with authentication and request handling.
 */

import type { ApiError } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Auth error callback for global handling
type AuthErrorCallback = () => void;
let onAuthErrorCallback: AuthErrorCallback | null = null;

export function setAuthErrorHandler(callback: AuthErrorCallback): void {
  onAuthErrorCallback = callback;
}

export function getAuthErrorHandler(): AuthErrorCallback | null {
  return onAuthErrorCallback;
}

export class AuthenticationError extends Error {
  constructor(message: string = 'Authentication failed') {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class ApiClient {
  private token: string | null = null;

  /**
   * Set the authentication token.
   */
  setToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  /**
   * Get the current authentication token.
   */
  getToken(): string | null {
    if (!this.token && typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  /**
   * Clear the authentication token.
   */
  clearToken(): void {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user_type');
      localStorage.removeItem('user_id');
    }
  }

  /**
   * Get the API base URL.
   */
  getBaseUrl(): string {
    return API_BASE;
  }

  /**
   * Make an API request.
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'Request failed',
      }));

      // Handle 401 Unauthorized - token expired or invalid
      if (response.status === 401) {
        this.clearToken();
        if (onAuthErrorCallback) {
          onAuthErrorCallback();
        }
        throw new AuthenticationError(error.detail || 'Session expired. Please log in again.');
      }

      throw new Error(error.detail);
    }

    return response.json();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
