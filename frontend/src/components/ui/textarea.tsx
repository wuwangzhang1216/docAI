import * as React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
  errorMessage?: string
  helperText?: string
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, errorMessage, helperText, ...props }, ref) => {
    return (
      <div className="w-full">
        <textarea
          className={cn(
            'flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200 resize-none',
            error && 'border-destructive focus-visible:ring-destructive',
            className
          )}
          ref={ref}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            errorMessage ? `${props.id}-error` : helperText ? `${props.id}-helper` : undefined
          }
          {...props}
        />

        {((error && errorMessage) || (!error && helperText)) && (
          <div className="mt-1.5 px-1">
            {error && errorMessage && (
              <p
                id={props.id ? `${props.id}-error` : undefined}
                className="text-xs text-destructive"
                role="alert"
              >
                {errorMessage}
              </p>
            )}
            {!error && helperText && (
              <p
                id={props.id ? `${props.id}-helper` : undefined}
                className="text-xs text-muted-foreground"
              >
                {helperText}
              </p>
            )}
          </div>
        )}
      </div>
    )
  }
)
Textarea.displayName = 'Textarea'

export { Textarea }
