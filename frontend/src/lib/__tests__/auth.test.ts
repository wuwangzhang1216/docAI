import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuth, getRedirectPath, isRouteAllowed } from '../auth'
import { act } from '@testing-library/react'

// Mock the api module
vi.mock('../api', () => ({
  api: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    validateToken: vi.fn(),
  },
  setAuthErrorHandler: vi.fn(),
}))

import { api } from '../api'

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset the store before each test
    useAuth.setState({
      isAuthenticated: false,
      userType: null,
      userId: null,
      isLoading: true,
      sessionExpired: false,
      passwordMustChange: false,
    })

    // Clear localStorage
    localStorage.clear()

    // Reset mocks
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('sets authentication state on successful login', async () => {
      const mockResponse = {
        access_token: 'test-token',
        user_type: 'PATIENT' as const,
        user_id: 'user-123',
        password_must_change: false,
      }

      vi.mocked(api.login).mockResolvedValueOnce(mockResponse)

      const { login } = useAuth.getState()
      await act(async () => {
        await login('test@example.com', 'password123')
      })

      const state = useAuth.getState()
      expect(state.isAuthenticated).toBe(true)
      expect(state.userType).toBe('PATIENT')
      expect(state.userId).toBe('user-123')
    })

    it('sets passwordMustChange flag when required', async () => {
      const mockResponse = {
        access_token: 'test-token',
        user_type: 'PATIENT' as const,
        user_id: 'user-123',
        password_must_change: true,
      }

      vi.mocked(api.login).mockResolvedValueOnce(mockResponse)

      const { login } = useAuth.getState()
      const result = await act(async () => {
        return await login('test@example.com', 'password123')
      })

      expect(result?.passwordMustChange).toBe(true)
      expect(useAuth.getState().passwordMustChange).toBe(true)
    })
  })

  describe('logout', () => {
    it('clears authentication state', async () => {
      useAuth.setState({
        isAuthenticated: true,
        userType: 'PATIENT',
        userId: 'user-123',
      })

      const { logout } = useAuth.getState()
      await act(async () => {
        await logout()
      })

      const state = useAuth.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.userType).toBeNull()
      expect(state.userId).toBeNull()
      expect(api.logout).toHaveBeenCalled()
    })
  })

  describe('handleAuthError', () => {
    it('sets sessionExpired flag', () => {
      useAuth.setState({
        isAuthenticated: true,
        userType: 'PATIENT',
        userId: 'user-123',
      })

      const { handleAuthError } = useAuth.getState()
      act(() => {
        handleAuthError()
      })

      const state = useAuth.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.sessionExpired).toBe(true)
    })
  })

  describe('clearSessionExpired', () => {
    it('clears the sessionExpired flag', () => {
      useAuth.setState({ sessionExpired: true })

      const { clearSessionExpired } = useAuth.getState()
      act(() => {
        clearSessionExpired()
      })

      expect(useAuth.getState().sessionExpired).toBe(false)
    })
  })
})

describe('getRedirectPath', () => {
  it('returns /dashboard for PATIENT', () => {
    expect(getRedirectPath('PATIENT')).toBe('/dashboard')
  })

  it('returns /patients for DOCTOR', () => {
    expect(getRedirectPath('DOCTOR')).toBe('/patients')
  })

  it('returns /admin for ADMIN', () => {
    expect(getRedirectPath('ADMIN')).toBe('/admin')
  })

  it('returns /login for null', () => {
    expect(getRedirectPath(null)).toBe('/login')
  })
})

describe('isRouteAllowed', () => {
  describe('for PATIENT', () => {
    it('allows patient routes', () => {
      expect(isRouteAllowed('/chat', 'PATIENT')).toBe(true)
      expect(isRouteAllowed('/checkin', 'PATIENT')).toBe(true)
      expect(isRouteAllowed('/assessment', 'PATIENT')).toBe(true)
      expect(isRouteAllowed('/history', 'PATIENT')).toBe(true)
    })

    it('denies doctor routes', () => {
      expect(isRouteAllowed('/patients', 'PATIENT')).toBe(false)
      expect(isRouteAllowed('/risk-queue', 'PATIENT')).toBe(false)
    })
  })

  describe('for DOCTOR', () => {
    it('allows doctor routes', () => {
      expect(isRouteAllowed('/patients', 'DOCTOR')).toBe(true)
      expect(isRouteAllowed('/risk-queue', 'DOCTOR')).toBe(true)
      expect(isRouteAllowed('/notes', 'DOCTOR')).toBe(true)
    })

    it('denies patient routes', () => {
      expect(isRouteAllowed('/chat', 'DOCTOR')).toBe(false)
      expect(isRouteAllowed('/checkin', 'DOCTOR')).toBe(false)
    })
  })

  describe('for ADMIN', () => {
    it('allows all routes', () => {
      expect(isRouteAllowed('/chat', 'ADMIN')).toBe(true)
      expect(isRouteAllowed('/patients', 'ADMIN')).toBe(true)
      expect(isRouteAllowed('/any-route', 'ADMIN')).toBe(true)
    })
  })

  describe('for null user', () => {
    it('denies all routes', () => {
      expect(isRouteAllowed('/chat', null)).toBe(false)
      expect(isRouteAllowed('/patients', null)).toBe(false)
    })
  })
})
