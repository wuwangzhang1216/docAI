'use client'

import { useI18n, type Locale } from '@/lib/i18n'
import { locales, localeNames } from '@/i18n/config'
import { cn } from '@/lib/utils'
import {
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption,
  Transition,
} from '@headlessui/react'
import { ChevronDown } from 'lucide-react'

interface LanguageSwitcherProps {
  className?: string
}

export function LanguageSwitcher({ className }: LanguageSwitcherProps) {
  const { locale, setLocale } = useI18n()

  return (
    <Listbox value={locale} onChange={(value) => setLocale(value as Locale)}>
      <div className="relative">
        <ListboxButton
          className={cn(
            'flex items-center gap-1 text-sm text-muted-foreground hover:text-primary px-2 py-1 rounded transition-colors',
            className
          )}
        >
          <span>{localeNames[locale]}</span>
          <ChevronDown className="w-4 h-4 transition-transform ui-open:rotate-180" />
        </ListboxButton>

        <Transition
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <ListboxOptions className="absolute top-full mt-1 right-0 bg-card border border-border rounded-lg shadow-lg py-1 z-50 min-w-[160px] max-h-[320px] overflow-y-auto focus:outline-none">
            {locales.map((loc) => (
              <ListboxOption
                key={loc}
                value={loc}
                className={({ focus, selected }) =>
                  cn(
                    'w-full text-left px-3 py-2 text-sm cursor-pointer transition-colors',
                    focus && 'bg-muted',
                    selected ? 'bg-primary/10 text-primary font-medium' : 'text-foreground'
                  )
                }
              >
                {localeNames[loc]}
              </ListboxOption>
            ))}
          </ListboxOptions>
        </Transition>
      </div>
    </Listbox>
  )
}
