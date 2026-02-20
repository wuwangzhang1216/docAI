'use client'

import { useState } from 'react'
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/react'
import { Loader2, CheckCircle2, ChevronDown, AlertCircle, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { HeartGuardianLogo } from '@/components/ui/HeartGuardianLogo'
import { MarkdownRenderer } from './MarkdownRenderer'

// Tool name to display name mapping
const TOOL_DISPLAY_NAMES: Record<string, string> = {
  get_mood_trends: 'Analyzed mood patterns',
  get_sleep_patterns: 'Checked sleep data',
  get_assessment_results: 'Reviewed assessments',
  get_coping_strategies: 'Found coping strategies',
  get_known_triggers: 'Checked triggers',
  get_recent_conversation_summary: 'Reviewed past conversations',
}

const TOOL_RUNNING_NAMES: Record<string, string> = {
  get_mood_trends: 'Analyzing mood patterns...',
  get_sleep_patterns: 'Checking sleep data...',
  get_assessment_results: 'Reviewing assessments...',
  get_coping_strategies: 'Finding coping strategies...',
  get_known_triggers: 'Checking triggers...',
  get_recent_conversation_summary: 'Reviewing past conversations...',
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
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={cn('flex gap-3 animate-message-left group', className)}>
      {/* AI Avatar - HeartGuardianLogo */}
      <div className="w-7 h-7 shrink-0 mt-1">
        <HeartGuardianLogo size={28} />
      </div>

      <div className="flex-1 min-w-0">
        {/* Tool calls display */}
        {toolCalls.length > 0 && (
          <div className="mb-2">
            {toolCalls.map((tool) => (
              <ToolCallItem key={tool.id} tool={tool} />
            ))}
          </div>
        )}

        {/* Message content - flat, no bubble */}
        {(content || (isStreaming && toolCalls.length === 0)) && (
          <div>
            {content ? (
              <MarkdownRenderer content={content} />
            ) : (
              /* Shimmer loading indicator */
              <div className="space-y-2">
                <div className="h-4 w-48 rounded animate-shimmer" />
                <div className="h-4 w-32 rounded animate-shimmer" />
              </div>
            )}

            {/* Streaming cursor */}
            {isStreaming && content && (
              <span className="inline-block w-1.5 h-5 ml-0.5 bg-foreground/50 animate-cursor-blink rounded-sm align-text-bottom" />
            )}
          </div>
        )}

        {/* Waiting for tool results - shimmer after tools */}
        {isStreaming &&
          !content &&
          toolCalls.length > 0 &&
          toolCalls.every((t) => t.status === 'completed') && (
            <div className="space-y-2 mt-1">
              <div className="h-4 w-48 rounded animate-shimmer" />
              <div className="h-4 w-32 rounded animate-shimmer" />
            </div>
          )}

        {/* Copy action bar - visible on hover */}
        {!isStreaming && content && (
          <div className="flex items-center gap-1 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors"
              aria-label="Copy message"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
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
  const isRunning = tool.status === 'running'

  if (isRunning) {
    const runningName = TOOL_RUNNING_NAMES[tool.name] || `${tool.name}...`
    return (
      <div className="flex items-center gap-2 py-1.5 text-sm text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin text-primary" />
        <span>{runningName}</span>
      </div>
    )
  }

  const displayName = TOOL_DISPLAY_NAMES[tool.name] || tool.name

  return (
    <Disclosure>
      {({ open }) => (
        <div className="my-0.5">
          <DisclosureButton className="flex items-center gap-2 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors w-full text-left">
            <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
            <span>{displayName}</span>
            {tool.resultPreview && (
              <ChevronDown
                className={cn(
                  'w-3.5 h-3.5 ml-auto transition-transform duration-200',
                  open && 'rotate-180'
                )}
              />
            )}
          </DisclosureButton>
          {tool.resultPreview && (
            <DisclosurePanel className="pl-6 pb-2 text-xs text-muted-foreground/80 border-l-2 border-border ml-2 leading-relaxed">
              {tool.resultPreview}
            </DisclosurePanel>
          )}
        </div>
      )}
    </Disclosure>
  )
}

// Error message component
export function ErrorMessage({ message, className }: { message: string; className?: string }) {
  return (
    <div className={cn('flex gap-3 animate-message-left', className)}>
      <div className="w-7 h-7 shrink-0 mt-1 flex items-center justify-center rounded-full bg-destructive/10">
        <AlertCircle className="w-4 h-4 text-destructive" />
      </div>

      <div className="text-sm text-destructive bg-destructive/5 border border-destructive/10 rounded-xl px-4 py-3">
        {message}
      </div>
    </div>
  )
}
