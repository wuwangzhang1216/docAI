'use client'

import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

const toastVariants = cva(
  'group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-lg border p-4 pr-8 shadow-lg transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full',
  {
    variants: {
      variant: {
        default: 'border bg-background text-foreground',
        success: 'border-success/20 bg-success/10 text-foreground',
        error: 'border-destructive/20 bg-destructive/10 text-foreground',
        warning: 'border-warning/20 bg-warning/10 text-foreground',
        info: 'border-info/20 bg-info/10 text-foreground',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

const iconMap = {
  default: Info,
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
}

const iconColorMap = {
  default: 'text-foreground',
  success: 'text-success',
  error: 'text-destructive',
  warning: 'text-warning',
  info: 'text-info',
}

export interface ToastProps
  extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof toastVariants> {
  title?: string
  description?: string
  onClose?: () => void
}

const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ className, variant = 'default', title, description, onClose, ...props }, ref) => {
    const Icon = iconMap[variant || 'default']
    const iconColor = iconColorMap[variant || 'default']

    return (
      <div
        ref={ref}
        className={cn(toastVariants({ variant }), className)}
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        {...props}
      >
        <div className="flex items-start gap-3">
          <Icon className={cn('h-5 w-5 flex-shrink-0 mt-0.5', iconColor)} />
          <div className="flex-1 space-y-1">
            {title && <p className="text-sm font-semibold">{title}</p>}
            {description && <p className="text-sm opacity-90">{description}</p>}
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="absolute right-2 top-2 rounded-md p-1 opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="关闭通知"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    )
  }
)

Toast.displayName = 'Toast'

export { Toast, toastVariants }
