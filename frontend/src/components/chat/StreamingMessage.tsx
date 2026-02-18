'use client'

import { useState, useEffect, useRef } from 'react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { cn } from '@/lib/utils'
import { Loader2, Wrench, CheckCircle2, AlertCircle } from 'lucide-react'

// Tool name to display name mapping
const TOOL_DISPLAY_NAMES: Record<string, string> = {
  get_mood_trends: 'Analyzing mood patterns',
  get_sleep_patterns: 'Checking sleep data',
  get_assessment_results: 'Reviewing assessments',
  get_coping_strategies: 'Finding coping strategies',
  get_known_triggers: 'Checking triggers',
  get_recent_conversation_summary: 'Reviewing past conversations',
}

interface ToolCall {
  id: string
  name: string
  status: 'running' | 'completed'
  resultPreview?: string
}

interface StreamingMessageProps {
  isStreaming: boolean
  content: string
  toolCalls: ToolCall[]
  className?: string
}

export function StreamingMessage({
  isStreaming,
  content,
  toolCalls,
  className,
}: StreamingMessageProps) {
  const contentRef = useRef<HTMLDivElement>(null)

  // Auto-scroll as content updates
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [content])

  return (
    <div className={cn('flex gap-3 animate-message-left', className)}>
      <Avatar className="w-8 h-8 shrink-0">
        <AvatarFallback className="bg-muted">AI</AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-2 max-w-[80%]">
        {/* Tool calls display */}
        {toolCalls.length > 0 && (
          <div className="space-y-1.5">
            {toolCalls.map((tool) => (
              <ToolCallItem key={tool.id} tool={tool} />
            ))}
          </div>
        )}

        {/* Message content */}
        {(content || isStreaming) && (
          <div
            ref={contentRef}
            className={cn(
              'bg-card text-card-foreground border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm',
              'text-sm leading-relaxed'
            )}
          >
            {content ? (
              <p className="whitespace-pre-wrap">{content}</p>
            ) : isStreaming && toolCalls.length === 0 ? (
              <div className="flex items-center space-x-1">
                <div
                  className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce"
                  style={{ animationDelay: '0s' }}
                />
                <div
                  className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                />
                <div
                  className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
              </div>
            ) : null}

            {/* Streaming cursor */}
            {isStreaming && content && (
              <span className="inline-block w-2 h-4 ml-0.5 bg-primary/60 animate-pulse" />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

interface ToolCallItemProps {
  tool: ToolCall
}

function ToolCallItem({ tool }: ToolCallItemProps) {
  const displayName = TOOL_DISPLAY_NAMES[tool.name] || tool.name
  const isRunning = tool.status === 'running'

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-2 rounded-lg text-xs',
        'bg-muted/50 border border-border/50',
        'transition-all duration-200',
        isRunning && 'animate-pulse'
      )}
    >
      {isRunning ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
      ) : (
        <CheckCircle2 className="w-3.5 h-3.5 text-success" />
      )}

      <Wrench className="w-3 h-3 text-muted-foreground" />

      <span className="text-muted-foreground">{isRunning ? displayName : `${displayName}`}</span>

      {!isRunning && tool.resultPreview && (
        <span className="text-muted-foreground/70 truncate max-w-[200px]">- Done</span>
      )}
    </div>
  )
}

// Thinking indicator component (like Claude.ai)
export function ThinkingIndicator({ className }: { className?: string }) {
  return (
    <div className={cn('flex gap-3 animate-message-left', className)}>
      <Avatar className="w-8 h-8 shrink-0">
        <AvatarFallback className="bg-muted">AI</AvatarFallback>
      </Avatar>

      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/30 border border-border/30">
        <Loader2 className="w-4 h-4 animate-spin text-primary" />
        <span className="text-sm text-muted-foreground">Thinking...</span>
      </div>
    </div>
  )
}

// Error message component
export function ErrorMessage({ message, className }: { message: string; className?: string }) {
  return (
    <div className={cn('flex gap-3 animate-message-left', className)}>
      <Avatar className="w-8 h-8 shrink-0">
        <AvatarFallback className="bg-destructive/10 text-destructive">
          <AlertCircle className="w-4 h-4" />
        </AvatarFallback>
      </Avatar>

      <div className="bg-destructive/10 text-destructive border border-destructive/20 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm text-sm">
        {message}
      </div>
    </div>
  )
}
