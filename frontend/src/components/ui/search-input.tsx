'use client';

import * as React from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from './input';

export interface SearchInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  value: string;
  onChange: (value: string) => void;
  debounceMs?: number;
  onClear?: () => void;
}

export function SearchInput({
  value,
  onChange,
  debounceMs = 300,
  onClear,
  className,
  placeholder = 'Search...',
  ...props
}: SearchInputProps) {
  const [localValue, setLocalValue] = React.useState(value);
  const debounceRef = React.useRef<NodeJS.Timeout | null>(null);

  // Sync local value with external value
  React.useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setLocalValue(newValue);

      // Clear existing timeout
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      // Set new debounced update
      debounceRef.current = setTimeout(() => {
        onChange(newValue);
      }, debounceMs);
    },
    [onChange, debounceMs]
  );

  const handleClear = React.useCallback(() => {
    setLocalValue('');
    onChange('');
    onClear?.();
  }, [onChange, onClear]);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return (
    <div className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
      <Input
        type="text"
        value={localValue}
        onChange={handleChange}
        placeholder={placeholder}
        className="pl-9 pr-8"
        {...props}
      />
      {localValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
