/**
 * Authentication utilities and hooks.
 */

import { create } from 'zustand';
import { api, setAuthErrorHandler } from './api';

type UserType = 'PATIENT' | 'DOCTOR' | 'ADMIN' | null;

interface AuthState {
  isAuthenticated: boolean;
  userType: UserType;
  userId: string | null;
  isLoading: boolean;
  sessionExpired: boolean;
  passwordMustChange: boolean;
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<{ passwordMustChange: boolean }>;
  register: (
    email: string,
    password: string,
    userType: 'PATIENT' | 'DOCTOR',
    firstName: string,
    lastName: string
  ) => Promise<void>;
  logout: () => Promise<void>;
  handleAuthError: () => void;
  clearSessionExpired: () => void;
  clearAuth: () => void;
  clearPasswordMustChange: () => void;
}

/**
 * Auth store using Zustand for state management.
 */
export const useAuth = create<AuthState>((set, get) => ({
  isAuthenticated: false,
  userType: null,
  userId: null,
  isLoading: true,
  sessionExpired: false,
  passwordMustChange: false,

  /**
   * Initialize auth state from localStorage and validate token with backend.
   */
  initialize: async () => {
    if (typeof window === 'undefined') {
      set({ isLoading: false });
      return;
    }

    // Set up the auth error handler to trigger logout on 401
    setAuthErrorHandler(() => {
      get().handleAuthError();
    });

    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('user_type') as UserType;
    const userId = localStorage.getItem('user_id');

    if (token && userType) {
      // Validate token with the backend
      const validatedUser = await api.validateToken();

      if (validatedUser) {
        // Token is valid - update state with fresh data from server
        const serverUserType = validatedUser.user_type as UserType;
        if (serverUserType) {
          localStorage.setItem('user_type', serverUserType);
        }

        set({
          isAuthenticated: true,
          userType: serverUserType,
          userId: validatedUser.id,
          isLoading: false,
          sessionExpired: false,
        });
      } else {
        // Token is invalid or expired - clear everything
        api.logout();
        set({
          isAuthenticated: false,
          userType: null,
          userId: null,
          isLoading: false,
          sessionExpired: true,
        });
      }
    } else {
      set({ isLoading: false, sessionExpired: false });
    }
  },

  /**
   * Login with email and password.
   * Returns whether password must be changed.
   */
  login: async (email: string, password: string) => {
    const response = await api.login(email, password);
    const passwordMustChange = response.password_must_change || false;

    set({
      isAuthenticated: true,
      userType: response.user_type,
      userId: response.user_id,
      passwordMustChange,
    });

    return { passwordMustChange };
  },

  /**
   * Register a new user.
   */
  register: async (
    email: string,
    password: string,
    userType: 'PATIENT' | 'DOCTOR',
    firstName: string,
    lastName: string
  ) => {
    const response = await api.register(email, password, userType, firstName, lastName);
    set({
      isAuthenticated: true,
      userType: response.user_type,
      userId: response.user_id,
    });
  },

  /**
   * Logout the current user.
   * Calls backend to invalidate token, then clears local state.
   */
  logout: async () => {
    await api.logout();
    set({
      isAuthenticated: false,
      userType: null,
      userId: null,
      sessionExpired: false,
    });
  },

  /**
   * Handle authentication errors (e.g., 401 from API).
   * This is called automatically when the API returns 401.
   */
  handleAuthError: () => {
    api.logout();
    set({
      isAuthenticated: false,
      userType: null,
      userId: null,
      sessionExpired: true,
    });
  },

  /**
   * Clear the session expired flag (after showing message to user).
   */
  clearSessionExpired: () => {
    set({ sessionExpired: false });
  },

  /**
   * Clear all auth state.
   */
  clearAuth: () => {
    api.logout();
    set({
      isAuthenticated: false,
      userType: null,
      userId: null,
      sessionExpired: false,
      passwordMustChange: false,
    });
  },

  /**
   * Clear the password must change flag (after password is changed).
   */
  clearPasswordMustChange: () => {
    set({ passwordMustChange: false });
  },
}));

/**
 * Get the redirect path based on user type.
 */
export function getRedirectPath(userType: UserType): string {
  switch (userType) {
    case 'PATIENT':
      return '/dashboard';
    case 'DOCTOR':
      return '/patients';
    case 'ADMIN':
      return '/admin';
    default:
      return '/login';
  }
}

/**
 * Check if the current route is allowed for the user type.
 */
export function isRouteAllowed(pathname: string, userType: UserType): boolean {
  const patientRoutes = ['/chat', '/checkin', '/assessment', '/history'];
  const doctorRoutes = ['/patients', '/risk-queue', '/notes'];

  if (userType === 'PATIENT') {
    return patientRoutes.some((route) => pathname.startsWith(route));
  }

  if (userType === 'DOCTOR') {
    return doctorRoutes.some((route) => pathname.startsWith(route));
  }

  if (userType === 'ADMIN') {
    return true;
  }

  return false;
}
