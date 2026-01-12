import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
    extends React.InputHTMLAttributes<HTMLInputElement> {
    error?: boolean
    errorMessage?: string
    helperText?: string
    leftIcon?: React.ReactNode
    rightIcon?: React.ReactNode
    showCharCount?: boolean
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, type, error, errorMessage, helperText, leftIcon, rightIcon, showCharCount, maxLength, value, ...props }, ref) => {
        const charCount = typeof value === 'string' ? value.length : 0

        return (
            <div className="w-full">
                <div className="relative">
                    {leftIcon && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" aria-hidden="true">
                            {leftIcon}
                        </div>
                    )}
                    <input
                        type={type}
                        className={cn(
                            "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
                            leftIcon && "pl-10",
                            rightIcon && "pr-10",
                            error && "border-destructive focus-visible:ring-destructive",
                            className
                        )}
                        ref={ref}
                        maxLength={maxLength}
                        value={value}
                        aria-invalid={error ? "true" : "false"}
                        aria-describedby={
                            errorMessage ? `${props.id}-error` :
                            helperText ? `${props.id}-helper` : undefined
                        }
                        {...props}
                    />
                    {rightIcon && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground" aria-hidden="true">
                            {rightIcon}
                        </div>
                    )}
                </div>

                {/* Helper text or error message - only render if needed */}
                {((error && errorMessage) || (!error && helperText) || (showCharCount && maxLength)) && (
                    <div className="flex justify-between items-start mt-1.5 px-1">
                        <div className="flex-1">
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

                        {/* Character count */}
                        {showCharCount && maxLength && (
                            <p className={cn(
                                "text-xs ml-2 flex-shrink-0",
                                charCount >= maxLength ? "text-destructive" : "text-muted-foreground"
                            )}>
                                {charCount}/{maxLength}
                            </p>
                        )}
                    </div>
                )}
            </div>
        )
    }
)
Input.displayName = "Input"

export { Input }
