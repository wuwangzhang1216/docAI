'use client'

import { useState, useRef, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { api, DoctorConversationListItem, DoctorConversationMessage } from '@/lib/api'
import {
  SendIcon,
  BotIcon,
  UserIcon,
  ArrowLeftIcon,
  HistoryIcon,
  PlusIcon,
  Loader2Icon,
  SparklesIcon,
  ChevronRightIcon,
} from '@/components/ui/icons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface PatientInfo {
  id: string
  first_name: string
  last_name: string
  full_name?: string
}

export default function DoctorAIAssistantPage() {
  const params = useParams()
  const router = useRouter()
  const patientId = params.id as string
  const t = useTranslations('doctor.aiAssistant')
  const common = useTranslations('common')

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [patientInfo, setPatientInfo] = useState<PatientInfo | null>(null)
  const [conversations, setConversations] = useState<DoctorConversationListItem[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [loadingPatient, setLoadingPatient] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch patient info
  useEffect(() => {
    const fetchPatient = async () => {
      try {
        const profile = await api.getPatientProfile(patientId)
        setPatientInfo(profile)
      } catch (error) {
        console.error('Error fetching patient:', error)
      } finally {
        setLoadingPatient(false)
      }
    }
    fetchPatient()
  }, [patientId])

  // Fetch conversation history
  const fetchConversations = async () => {
    setLoadingHistory(true)
    try {
      const data = await api.getDoctorAIConversations(patientId, 10)
      setConversations(data)
    } catch (error) {
      console.error('Error fetching conversations:', error)
    } finally {
      setLoadingHistory(false)
    }
  }

  // Load a previous conversation
  const loadConversation = async (convId: string) => {
    try {
      const detail = await api.getDoctorAIConversationDetail(patientId, convId)
      setMessages(
        detail.messages.map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
        }))
      )
      setConversationId(convId)
      setShowHistory(false)
    } catch (error) {
      console.error('Error loading conversation:', error)
    }
  }

  // Start a new conversation
  const startNewConversation = () => {
    setMessages([])
    setConversationId(null)
    setShowHistory(false)
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const res = await api.sendDoctorAIChat(patientId, userMessage, conversationId || undefined)

      setMessages((prev) => [...prev, { role: 'assistant', content: res.response }])
      setConversationId(res.conversation_id)
    } catch (error) {
      console.error('AI chat error:', error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: t('errorMessage', {
            defaultValue: 'Sorry, an error occurred. Please try again.',
          }),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const suggestedPrompts = [
    t('prompt1', { defaultValue: "Analyze this patient's mood trends over the past 2 weeks" }),
    t('prompt2', { defaultValue: 'What risk factors should I be aware of?' }),
    t('prompt3', { defaultValue: "Summarize the patient's recent check-ins" }),
    t('prompt4', { defaultValue: 'What treatment approaches might be helpful?' }),
  ]

  if (loadingPatient) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Breadcrumb */}
      <div className="px-4 py-2 border-b border-border">
        <Breadcrumb>
          <BreadcrumbItem>
            <BreadcrumbLink href="/patients">{common('back')}</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href={`/patients/${patientId}`}>
              {patientInfo?.first_name} {patientInfo?.last_name}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{t('title')}</BreadcrumbPage>
          </BreadcrumbItem>
        </Breadcrumb>
      </div>

      {/* Header */}
      <div className="bg-primary px-4 py-3 text-primary-foreground">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="p-1 hover:bg-white/10 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="bg-white/20 p-2 rounded-lg">
                <SparklesIcon className="w-5 h-5" />
              </div>
              <div>
                <h1 className="font-semibold">{t('title', { defaultValue: 'AI Assistant' })}</h1>
                <p className="text-sm text-white/80">
                  {patientInfo?.full_name || `${patientInfo?.first_name} ${patientInfo?.last_name}`}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowHistory(!showHistory)
                if (!showHistory) fetchConversations()
              }}
              className="text-white hover:bg-white/10"
            >
              <HistoryIcon className="w-4 h-4 mr-1" />
              {t('history', { defaultValue: 'History' })}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={startNewConversation}
              className="text-white hover:bg-white/10"
            >
              <PlusIcon className="w-4 h-4 mr-1" />
              {t('new', { defaultValue: 'New' })}
            </Button>
          </div>
        </div>
      </div>

      {/* History Sidebar */}
      {showHistory && (
        <div className="absolute right-0 top-0 bottom-0 w-80 bg-card border-l border-border shadow-xl z-50 flex flex-col">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h2 className="font-semibold text-foreground">
              {t('conversationHistory', { defaultValue: 'Conversation History' })}
            </h2>
            <button
              onClick={() => setShowHistory(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              <ChevronRightIcon className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {loadingHistory ? (
              <div className="flex items-center justify-center py-8">
                <Loader2Icon className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : conversations.length === 0 ? (
              <p className="text-center text-muted-foreground py-8 text-sm">
                {t('noHistory', { defaultValue: 'No previous conversations' })}
              </p>
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => loadConversation(conv.id)}
                    className={cn(
                      'w-full text-left p-3 rounded-lg transition-colors',
                      conv.id === conversationId
                        ? 'bg-primary/10 border border-primary/20'
                        : 'hover:bg-muted'
                    )}
                  >
                    <p className="text-sm font-medium text-foreground line-clamp-2">
                      {conv.summary || t('conversation', { defaultValue: 'Conversation' })}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(conv.created_at).toLocaleDateString()} · {conv.message_count}{' '}
                      {t('messages', { defaultValue: 'messages' })}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto relative">
        <div className="flex flex-col min-h-full p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <div className="w-20 h-20 bg-primary/10 rounded-2xl flex items-center justify-center mb-4">
                <BotIcon className="w-10 h-10 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">
                {t('welcomeTitle', { defaultValue: 'AI Clinical Assistant' })}
              </h3>
              <p className="max-w-md text-sm text-muted-foreground mb-6">
                {t('welcomeMessage', {
                  defaultValue:
                    "I can help you analyze this patient's data, identify patterns, and discuss treatment considerations. What would you like to know?",
                })}
              </p>

              {/* Suggested Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
                {suggestedPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(prompt)
                    }}
                    className="text-left p-3 rounded-lg border border-border bg-card hover:bg-muted transition-colors text-sm"
                  >
                    <p className="text-foreground line-clamp-2">{prompt}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={cn(
                    'flex gap-3',
                    msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  )}
                >
                  <Avatar className="w-8 h-8 shrink-0">
                    <AvatarFallback
                      className={
                        msg.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-primary text-primary-foreground'
                      }
                    >
                      {msg.role === 'user' ? (
                        <UserIcon className="w-4 h-4" />
                      ) : (
                        <BotIcon className="w-4 h-4" />
                      )}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={cn(
                      'max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm',
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-tr-sm'
                        : 'bg-card text-card-foreground border border-border rounded-tl-sm'
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex gap-3">
                  <Avatar className="w-8 h-8 shrink-0">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      <BotIcon className="w-4 h-4" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex items-center space-x-1">
                    <div
                      className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce"
                      style={{ animationDelay: '0s' }}
                    />
                    <div
                      className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce"
                      style={{ animationDelay: '0.1s' }}
                    />
                    <div
                      className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="bg-background/80 backdrop-blur-md p-4 border-t border-border">
        <form
          className="flex items-end space-x-2 max-w-3xl mx-auto"
          onSubmit={(e) => {
            e.preventDefault()
            sendMessage()
          }}
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('placeholder', { defaultValue: 'Ask about this patient...' })}
            className="rounded-full pl-6 pr-6 py-6 border-0 bg-muted/50 focus-visible:ring-1 focus-visible:bg-background shadow-inner resize-none"
            disabled={loading}
          />
          <Button
            type="submit"
            disabled={loading || !input.trim()}
            size="icon"
            className="h-12 w-12 rounded-full shrink-0 shadow-sm"
          >
            <SendIcon className="w-5 h-5 ml-0.5" />
          </Button>
        </form>
        <p className="text-xs text-muted-foreground text-center mt-2 max-w-3xl mx-auto">
          {t('disclaimer', {
            defaultValue:
              'AI suggestions are for informational purposes only. Clinical decisions remain with the treating physician.',
          })}
        </p>
      </div>
    </div>
  )
}
