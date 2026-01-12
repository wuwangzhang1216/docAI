'use client';

import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme, type Theme } from '@/lib/theme';
import { cn } from '@/lib/utils';

interface ThemeSwitcherProps {
  className?: string;
  showLabel?: boolean;
}

export function ThemeSwitcher({ className, showLabel = false }: ThemeSwitcherProps) {
  const { theme, setTheme, mounted } = useTheme();

  const themes: { value: Theme; icon: React.ElementType; label: string }[] = [
    { value: 'light', icon: Sun, label: '浅色' },
    { value: 'dark', icon: Moon, label: '深色' },
    { value: 'system', icon: Monitor, label: '系统' },
  ];

  // 避免服务端渲染时的闪烁
  if (!mounted) {
    return (
      <div className={cn('flex items-center', className)}>
        <div className="flex items-center bg-muted rounded-lg p-1">
          <div className="w-[120px] h-8 animate-pulse bg-muted-foreground/20 rounded-md" />
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex items-center', className)}>
      <div className="flex items-center bg-muted rounded-lg p-1">
        {themes.map(({ value, icon: Icon, label }) => (
          <button
            key={value}
            onClick={() => setTheme(value)}
            className={cn(
              'flex items-center gap-1.5 px-2 py-1.5 rounded-md text-sm font-medium transition-all duration-200',
              theme === value
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
            title={label}
            aria-label={`切换到${label}模式`}
            aria-pressed={theme === value}
          >
            <Icon className="w-4 h-4" />
            {showLabel && <span className="hidden sm:inline">{label}</span>}
          </button>
        ))}
      </div>
    </div>
  );
}

// Simple toggle button for compact spaces
export function ThemeToggle({ className }: { className?: string }) {
  const { isDark, setTheme, mounted } = useTheme();

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark');
  };

  // 避免服务端渲染时的闪烁
  if (!mounted) {
    return (
      <button
        className={cn('p-2 rounded-lg', className)}
        disabled
      >
        <div className="w-5 h-5 animate-pulse bg-muted-foreground/20 rounded" />
      </button>
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'p-2 rounded-lg transition-colors hover:bg-muted',
        className
      )}
      aria-label={isDark ? '切换到浅色模式' : '切换到深色模式'}
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-yellow-500" />
      ) : (
        <Moon className="w-5 h-5 text-muted-foreground" />
      )}
    </button>
  );
}
