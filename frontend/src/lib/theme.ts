'use client';

import { useEffect, useState, useCallback } from 'react';

export type Theme = 'light' | 'dark' | 'system';

const THEME_KEY = 'theme-preference';

// Get theme from localStorage
function getStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'light';
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored;
  }
  return 'light'; // 默认浅色模式
}

// Get system preference
function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

// Apply theme to document
function applyThemeToDocument(theme: Theme) {
  if (typeof document === 'undefined') return 'light';

  const root = document.documentElement;
  const resolvedTheme = theme === 'system' ? getSystemTheme() : theme;

  // Remove previous theme class
  root.classList.remove('light', 'dark');
  // Add new theme class
  root.classList.add(resolvedTheme);

  // Update meta theme-color
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute(
      'content',
      resolvedTheme === 'dark' ? '#0f172a' : '#3b82f6'
    );
  }

  return resolvedTheme;
}

// Hook for using theme
export function useTheme() {
  const [theme, setThemeState] = useState<Theme>('light');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  // Initialize on mount
  useEffect(() => {
    const storedTheme = getStoredTheme();
    setThemeState(storedTheme);
    const resolved = applyThemeToDocument(storedTheme);
    setResolvedTheme(resolved);
    setMounted(true);
  }, []);

  // Listen for system theme changes
  useEffect(() => {
    if (!mounted) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        const resolved = applyThemeToDocument('system');
        setResolvedTheme(resolved);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, mounted]);

  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem(THEME_KEY, newTheme);
    const resolved = applyThemeToDocument(newTheme);
    setResolvedTheme(resolved);
  }, []);

  return {
    theme,
    setTheme,
    resolvedTheme,
    isDark: resolvedTheme === 'dark',
    mounted,
  };
}

// Script to prevent flash - 在 HTML head 中内联执行
export const themeScript = `
(function() {
  try {
    var theme = localStorage.getItem('${THEME_KEY}') || 'light';
    var resolved = theme;
    if (theme === 'system') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.classList.add(resolved);
  } catch (e) {}
})();
`;
