'use client';

import * as React from 'react';
import {
  Disclosure as HeadlessDisclosure,
  DisclosureButton as HeadlessDisclosureButton,
  DisclosurePanel as HeadlessDisclosurePanel,
} from '@headlessui/react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DisclosureProps {
  defaultOpen?: boolean;
  children: React.ReactNode | ((props: { open: boolean }) => React.ReactNode);
  className?: string;
}

const Disclosure = ({ defaultOpen = false, children, className }: DisclosureProps) => (
  <HeadlessDisclosure defaultOpen={defaultOpen}>
    {({ open }) => (
      <div className={cn('bg-card border border-border rounded-xl shadow-sm overflow-hidden', className)}>
        {typeof children === 'function' ? children({ open }) : children}
      </div>
    )}
  </HeadlessDisclosure>
);

interface DisclosureButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  children: React.ReactNode | ((props: { open: boolean }) => React.ReactNode);
  showChevron?: boolean;
}

const DisclosureButton = React.forwardRef<HTMLButtonElement, DisclosureButtonProps>(
  ({ children, className, showChevron = true, ...props }, ref) => (
    <HeadlessDisclosure.Button
      ref={ref}
      className={cn(
        'w-full p-4 flex items-center justify-between text-left hover:bg-muted transition-colors',
        className
      )}
      {...props}
    >
      {({ open }) => (
        <>
          {typeof children === 'function' ? children({ open }) : children}
          {showChevron && (
            open ? (
              <ChevronUp className="w-5 h-5 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            )
          )}
        </>
      )}
    </HeadlessDisclosure.Button>
  )
);
DisclosureButton.displayName = 'DisclosureButton';

interface DisclosurePanelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const DisclosurePanel = React.forwardRef<HTMLDivElement, DisclosurePanelProps>(
  ({ children, className, ...props }, ref) => (
    <HeadlessDisclosure.Panel
      ref={ref}
      className={cn('p-4 pt-0', className)}
      {...props}
    >
      {children}
    </HeadlessDisclosure.Panel>
  )
);
DisclosurePanel.displayName = 'DisclosurePanel';

export { Disclosure, DisclosureButton, DisclosurePanel };
