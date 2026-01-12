'use client';

import * as React from 'react';
import {
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption,
  Transition,
} from '@headlessui/react';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

const Select = ({
  value,
  onChange,
  options,
  placeholder = 'Select...',
  className,
  disabled = false,
}: SelectProps) => {
  const selectedOption = options.find((opt) => opt.value === value);

  return (
    <Listbox value={value} onChange={onChange} disabled={disabled}>
      <div className={cn('relative', className)}>
        <ListboxButton
          className={cn(
            'relative w-full border rounded-md px-3 py-2 text-sm text-left',
            'bg-background border-input',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            'disabled:cursor-not-allowed disabled:opacity-50',
            'flex items-center justify-between'
          )}
        >
          <span className={!selectedOption ? 'text-muted-foreground' : ''}>
            {selectedOption?.label || placeholder}
          </span>
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </ListboxButton>

        <Transition
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <ListboxOptions
            className={cn(
              'absolute z-50 mt-1 w-full',
              'bg-popover border border-border rounded-lg shadow-lg',
              'py-1',
              'focus:outline-none'
            )}
          >
            {options.map((option) => (
              <ListboxOption
                key={option.value}
                value={option.value}
                className={({ focus, selected }) =>
                  cn(
                    'relative cursor-pointer select-none py-2 px-3 text-sm',
                    focus && 'bg-accent',
                    selected && 'bg-primary/10 text-primary font-medium'
                  )
                }
              >
                {({ selected }) => (
                  <div className="flex items-center justify-between">
                    <span>{option.label}</span>
                    {selected && <Check className="w-4 h-4" />}
                  </div>
                )}
              </ListboxOption>
            ))}
          </ListboxOptions>
        </Transition>
      </div>
    </Listbox>
  );
};

export { Select };
