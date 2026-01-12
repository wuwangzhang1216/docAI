'use client';

import * as React from 'react';
import {
  Dialog as HeadlessDialog,
  DialogPanel as HeadlessDialogPanel,
  DialogTitle as HeadlessDialogTitle,
  DialogBackdrop as HeadlessDialogBackdrop,
  Transition,
  TransitionChild,
} from '@headlessui/react';
import { cn } from '@/lib/utils';

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

const Dialog = ({ open, onClose, children, className }: DialogProps) => (
  <Transition show={open}>
    <HeadlessDialog onClose={onClose} className={cn('relative z-50', className)}>
      {children}
    </HeadlessDialog>
  </Transition>
);

const DialogBackdrop = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <TransitionChild
    enter="ease-out duration-200"
    enterFrom="opacity-0"
    enterTo="opacity-100"
    leave="ease-in duration-150"
    leaveFrom="opacity-100"
    leaveTo="opacity-0"
  >
    <HeadlessDialogBackdrop
      ref={ref}
      className={cn(
        'fixed inset-0 bg-background/80 backdrop-blur-sm',
        className
      )}
      {...props}
    />
  </TransitionChild>
));
DialogBackdrop.displayName = 'DialogBackdrop';

interface DialogPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const DialogPanel = React.forwardRef<HTMLDivElement, DialogPanelProps>(
  ({ className, children, ...props }, ref) => (
    <div className="fixed inset-0 flex items-center justify-center p-4">
      <TransitionChild
        enter="ease-out duration-200"
        enterFrom="opacity-0 scale-95"
        enterTo="opacity-100 scale-100"
        leave="ease-in duration-150"
        leaveFrom="opacity-100 scale-100"
        leaveTo="opacity-0 scale-95"
      >
        <HeadlessDialogPanel
          ref={ref}
          className={cn(
            'bg-card text-card-foreground border border-border rounded-xl p-6 shadow-2xl w-full max-w-md',
            className
          )}
          {...props}
        >
          {children}
        </HeadlessDialogPanel>
      </TransitionChild>
    </div>
  )
);
DialogPanel.displayName = 'DialogPanel';

const DialogTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <HeadlessDialogTitle
    ref={ref}
    className={cn('text-lg font-semibold mb-4', className)}
    {...props}
  />
));
DialogTitle.displayName = 'DialogTitle';

export { Dialog, DialogBackdrop, DialogPanel, DialogTitle };
