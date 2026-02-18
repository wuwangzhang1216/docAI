'use client'

import { cn } from '@/lib/utils'

interface SegmentedControlOption<T extends string> {
  value: T
  label: string
  icon?: React.ElementType
}

interface SegmentedControlProps<T extends string> {
  value: T
  onChange: (value: T) => void
  options: SegmentedControlOption<T>[]
}

export function SegmentedControl<T extends string>({
  value,
  onChange,
  options,
}: SegmentedControlProps<T>) {
  return (
    <div className="flex gap-1 p-1 bg-muted rounded-xl">
      {options.map((option) => {
        const Icon = option.icon
        const isActive = value === option.value
        return (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 py-2.5 px-4 text-sm font-medium rounded-lg transition-colors',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {Icon && <Icon className="w-4 h-4" />}
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
