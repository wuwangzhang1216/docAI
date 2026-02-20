'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'
import { Send, ImagePlus, X, UserCheck, ArrowLeft, Loader2, Bot, Stethoscope } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from '@/components/ui/dialog'
import { ThreadList, MessageBubble, MessageInput } from '@/components/messaging'
import { ChatSkeleton } from '@/components/ui/skeleton'
import { useMessagingStore, type MessageType } from '@/lib/messaging'
import { useWebSocket, type WSMessage } from '@/hooks/useWebSocket'
import { cn } from '@/lib/utils'
import { SegmentedControl } from '@/components/ui/segmented-control'
import { StreamingMessage, ErrorMessage } from '@/components/chat/StreamingMessage'
import { HeartGuardianLogo } from '@/components/ui/HeartGuardianLogo'

interface ToolCall {
  id: string
  name: string
  status: 'running' | 'completed'
  resultPreview?: string
}

interface ImageAttachment {
  id: string
  previewUrl: string
  media_type: string
  data: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  toolCalls?: ToolCall[]
  error?: string
  images?: string[]
}

interface DoctorInfo {
  id: string
  full_name: string
  specialty?: string
}

const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
const MAX_IMAGE_SIZE = 5 * 1024 * 1024
const MAX_IMAGES = 4

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      resolve(result.split(',')[1])
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// AI Chat Component - Streaming with Markdown + Tool calls
function AIChat({ t }: { t: ReturnType<typeof useTranslations<'patient.chat'>> }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [showCrisisModal, setShowCrisisModal] = useState(false)
  const [connectedDoctor, setConnectedDoctor] = useState<DoctorInfo | null>(null)
  const [imageAttachments, setImageAttachments] = useState<ImageAttachment[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const suggestedPrompts = [
    t('suggestedPrompt1', {
      defaultValue: "I've been feeling anxious lately, can we talk about it?",
    }),
    t('suggestedPrompt2', { defaultValue: 'Help me understand my mood patterns this week' }),
    t('suggestedPrompt3', { defaultValue: 'I need some coping strategies for stress' }),
    t('suggestedPrompt4', { defaultValue: 'I had trouble sleeping, what can I do?' }),
  ]

  useEffect(() => {
    const checkConnectedDoctor = async () => {
      try {
        const doctor = await api.getMyDoctor()
        setConnectedDoctor(doctor)
      } catch {
        setConnectedDoctor(null)
      }
    }
    checkConnectedDoctor()
  }, [])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  }, [input])

  useEffect(() => {
    return () => {
      imageAttachments.forEach((att) => URL.revokeObjectURL(att.previewUrl))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleImageSelect = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return
      const newAttachments: ImageAttachment[] = []
      for (const file of Array.from(files)) {
        if (imageAttachments.length + newAttachments.length >= MAX_IMAGES) break
        if (!ALLOWED_IMAGE_TYPES.includes(file.type)) continue
        if (file.size > MAX_IMAGE_SIZE) continue
        const base64 = await fileToBase64(file)
        newAttachments.push({
          id: crypto.randomUUID(),
          previewUrl: URL.createObjectURL(file),
          media_type: file.type,
          data: base64,
        })
      }
      if (newAttachments.length > 0) {
        setImageAttachments((prev) => [...prev, ...newAttachments])
      }
      if (imageInputRef.current) imageInputRef.current.value = ''
    },
    [imageAttachments.length]
  )

  const removeImage = useCallback((id: string) => {
    setImageAttachments((prev) => {
      const att = prev.find((a) => a.id === id)
      if (att) URL.revokeObjectURL(att.previewUrl)
      return prev.filter((a) => a.id !== id)
    })
  }, [])

  const sendMessage = async (overrideMessage?: string) => {
    const messageText = overrideMessage || input.trim()
    if ((!messageText && imageAttachments.length === 0) || loading) return

    const userMessage = messageText || t('imageAttached', { defaultValue: '[Image]' })
    const currentImages = [...imageAttachments]
    const imagePreviewUrls = currentImages.map((a) => a.previewUrl)

    setInput('')
    setImageAttachments([])
    setLoading(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: userMessage,
        images: imagePreviewUrls.length > 0 ? imagePreviewUrls : undefined,
      },
      { role: 'assistant', content: '', isStreaming: true, toolCalls: [] },
    ])

    const assistantIndex = messages.length + 1
    const apiImages =
      currentImages.length > 0
        ? currentImages.map((a) => ({ media_type: a.media_type, data: a.data }))
        : undefined

    try {
      await api.sendMessageStream(
        userMessage,
        conversationId || undefined,
        {
          onToolStart: (toolId, toolName) => {
            setMessages((prev) => {
              const newMessages = [...prev]
              const lastMsg = newMessages[assistantIndex]
              if (lastMsg?.role === 'assistant') {
                lastMsg.toolCalls = [
                  ...(lastMsg.toolCalls || []),
                  { id: toolId, name: toolName, status: 'running' },
                ]
              }
              return [...newMessages]
            })
          },
          onToolEnd: (toolId, _toolName, resultPreview) => {
            setMessages((prev) => {
              const newMessages = [...prev]
              const lastMsg = newMessages[assistantIndex]
              if (lastMsg?.role === 'assistant' && lastMsg.toolCalls) {
                lastMsg.toolCalls = lastMsg.toolCalls.map((tc) =>
                  tc.id === toolId ? { ...tc, status: 'completed' as const, resultPreview } : tc
                )
              }
              return [...newMessages]
            })
          },
          onTextDelta: (text) => {
            setMessages((prev) => {
              const newMessages = [...prev]
              const lastMsg = newMessages[assistantIndex]
              if (lastMsg?.role === 'assistant') lastMsg.content += text
              return [...newMessages]
            })
          },
          onMessageComplete: (content) => {
            setMessages((prev) => {
              const newMessages = [...prev]
              const lastMsg = newMessages[assistantIndex]
              if (lastMsg?.role === 'assistant') {
                lastMsg.content = content
                lastMsg.isStreaming = false
              }
              return [...newMessages]
            })
          },
          onMetadata: (newConversationId, riskAlert) => {
            setConversationId(newConversationId)
            if (riskAlert) setShowCrisisModal(true)
          },
          onError: (errorMessage) => {
            setMessages((prev) => {
              const newMessages = [...prev]
              const lastMsg = newMessages[assistantIndex]
              if (lastMsg?.role === 'assistant') {
                lastMsg.error = errorMessage
                lastMsg.isStreaming = false
              }
              return [...newMessages]
            })
          },
        },
        apiImages
      )
    } catch (error) {
      console.error('Chat error:', error)
      setMessages((prev) => {
        const newMessages = [...prev]
        const lastMsg = newMessages[assistantIndex]
        if (lastMsg?.role === 'assistant') {
          lastMsg.error = t('errorMessage')
          lastMsg.isStreaming = false
        }
        return [...newMessages]
      })
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

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto" role="log" aria-live="polite">
        <div className="flex flex-col min-h-full max-w-3xl mx-auto px-4 py-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 max-w-lg mx-auto">
              <HeartGuardianLogo size={48} className="mb-5" />
              <h3 className="text-xl font-semibold mb-2 text-foreground">{t('welcomeTitle')}</h3>
              <p className="text-muted-foreground text-sm mb-8 max-w-xs">{t('welcomeMessage')}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full">
                {suggestedPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(prompt)}
                    className="text-left p-3.5 rounded-xl border border-border bg-card hover:bg-muted/50 transition-colors text-sm leading-relaxed"
                  >
                    <p className="text-foreground line-clamp-2">{prompt}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => {
                if (msg.role === 'user') {
                  return (
                    <div key={idx} className="flex justify-end animate-message-right">
                      <div className="max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed bg-muted text-foreground">
                        {msg.images && msg.images.length > 0 && (
                          <div
                            className={`flex gap-1.5 mb-2 ${msg.images.length === 1 ? '' : 'flex-wrap'}`}
                          >
                            {msg.images.map((url, imgIdx) => (
                              <img
                                key={imgIdx}
                                src={url}
                                alt=""
                                className="rounded-lg max-h-48 max-w-full object-cover"
                              />
                            ))}
                          </div>
                        )}
                        {msg.content &&
                          msg.content !== t('imageAttached', { defaultValue: '[Image]' }) && (
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                          )}
                      </div>
                    </div>
                  )
                }
                if (msg.error) return <ErrorMessage key={idx} message={msg.error} />
                return (
                  <StreamingMessage
                    key={idx}
                    isStreaming={msg.isStreaming || false}
                    content={msg.content}
                    toolCalls={msg.toolCalls || []}
                  />
                )
              })}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input area */}
      <div className="bg-background/80 backdrop-blur-md px-4 pb-3 pt-2">
        <div className="max-w-3xl mx-auto">
          {imageAttachments.length > 0 && (
            <div className="flex gap-2 mb-2 overflow-x-auto pb-1">
              {imageAttachments.map((att) => (
                <div key={att.id} className="relative flex-shrink-0 group/img">
                  <img
                    src={att.previewUrl}
                    alt=""
                    className="w-16 h-16 rounded-lg object-cover ring-1 ring-border"
                  />
                  <button
                    type="button"
                    onClick={() => removeImage(att.id)}
                    className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-destructive text-destructive-foreground rounded-full flex items-center justify-center opacity-0 group-hover/img:opacity-100 transition-opacity shadow-sm"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <form
            className="relative flex items-end gap-1 border border-border rounded-2xl bg-muted/30 px-2 py-1.5 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all shadow-sm"
            onSubmit={(e) => {
              e.preventDefault()
              sendMessage()
            }}
          >
            <input
              ref={imageInputRef}
              type="file"
              accept={ALLOWED_IMAGE_TYPES.join(',')}
              multiple
              className="hidden"
              onChange={(e) => handleImageSelect(e.target.files)}
              disabled={loading}
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => imageInputRef.current?.click()}
              disabled={loading || imageAttachments.length >= MAX_IMAGES}
              className="h-9 w-9 rounded-full shrink-0 text-muted-foreground hover:text-foreground"
            >
              <ImagePlus className="w-5 h-5" />
            </Button>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('placeholder')}
              rows={1}
              className="flex-1 resize-none bg-transparent border-0 outline-none text-sm leading-relaxed placeholder:text-muted-foreground max-h-[200px] py-2 px-2"
              disabled={loading}
            />
            <Button
              type="submit"
              disabled={loading || (!input.trim() && imageAttachments.length === 0)}
              size="icon"
              className="h-9 w-9 rounded-full shrink-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
          <p className="text-[11px] text-muted-foreground text-center mt-2">{t('disclaimer')}</p>
        </div>
      </div>

      {/* Crisis Modal */}
      <Dialog open={showCrisisModal} onClose={() => setShowCrisisModal(false)}>
        <DialogBackdrop />
        <DialogPanel>
          <DialogTitle className="text-destructive flex items-center">
            <span className="mr-2">🚨</span> {t('crisisTitle')}
          </DialogTitle>
          <p className="text-muted-foreground mb-4 text-sm leading-relaxed">{t('crisisMessage')}</p>
          <ul className="space-y-2 mb-4 text-sm font-medium bg-muted/50 p-4 rounded-lg">
            <li className="flex items-center text-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-destructive mr-2" />
              {t('crisisLine1')}
            </li>
            <li className="flex items-center text-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-destructive mr-2" />
              {t('crisisLine2')}
            </li>
          </ul>
          {connectedDoctor && (
            <div className="mb-4 p-3 bg-primary/10 rounded-lg flex items-center gap-2 text-sm">
              <UserCheck className="w-4 h-4 text-primary shrink-0" />
              <span className="text-foreground">
                {t('doctorNotified', {
                  doctorName: connectedDoctor.full_name,
                  defaultValue: `Dr. ${connectedDoctor.full_name} has been notified.`,
                })}
              </span>
            </div>
          )}
          <Button
            onClick={() => setShowCrisisModal(false)}
            className="w-full bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {t('crisisAck')}
          </Button>
        </DialogPanel>
      </Dialog>
    </div>
  )
}

// Doctor Messages Component
function DoctorMessages({ t }: { t: ReturnType<typeof useTranslations<'messaging'>> }) {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    threads,
    currentThread,
    isLoadingThreads,
    isLoadingMessages,
    loadThreads,
    loadThread,
    sendMessage,
    markAsRead,
    handleNewMessage,
    handleMessageRead,
    clearCurrentThread,
  } = useMessagingStore()

  const handleWSMessage = useCallback(
    (message: WSMessage) => {
      if (message.type === 'new_message' && message.payload) {
        handleNewMessage(message.payload as unknown as Parameters<typeof handleNewMessage>[0])
      } else if (message.type === 'message_read' && message.payload) {
        const payload = message.payload as unknown as {
          thread_id: string
          reader_type: 'DOCTOR' | 'PATIENT'
        }
        handleMessageRead(payload.thread_id, payload.reader_type)
      }
    },
    [handleNewMessage, handleMessageRead]
  )

  const { subscribeToThread, unsubscribeFromThread } = useWebSocket({
    onMessage: handleWSMessage,
    autoConnect: true,
  })

  useEffect(() => {
    loadThreads()
  }, [loadThreads])

  useEffect(() => {
    if (selectedThreadId) {
      loadThread(selectedThreadId)
      subscribeToThread(selectedThreadId)
      markAsRead(selectedThreadId)
    }

    return () => {
      if (selectedThreadId) {
        unsubscribeFromThread(selectedThreadId)
      }
    }
  }, [selectedThreadId, loadThread, subscribeToThread, unsubscribeFromThread, markAsRead])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentThread?.messages])

  const handleSelectThread = (threadId: string) => {
    setSelectedThreadId(threadId)
  }

  const handleBack = () => {
    setSelectedThreadId(null)
    clearCurrentThread()
  }

  const handleSendMessage = async (
    content: string,
    messageType: MessageType,
    attachmentIds?: string[]
  ) => {
    if (!selectedThreadId) return
    await sendMessage(selectedThreadId, content, messageType, attachmentIds)
  }

  const handleLoadMore = () => {
    if (selectedThreadId && currentThread?.has_more) {
      loadThread(selectedThreadId, true)
    }
  }

  if (!selectedThreadId) {
    return (
      <div className="flex flex-col h-full">
        <ThreadList
          threads={threads}
          onSelectThread={handleSelectThread}
          loading={isLoadingThreads}
        />
      </div>
    )
  }

  const threadInfo = currentThread || threads.find((th) => th.id === selectedThreadId)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border bg-background flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={handleBack} className="shrink-0">
          <ArrowLeft className="w-5 h-5" />
        </Button>

        <Avatar className="w-10 h-10 shrink-0">
          <AvatarFallback className="bg-blue-500/10 text-blue-600 dark:text-blue-400">
            {threadInfo?.other_party_name?.charAt(0).toUpperCase() || 'D'}
          </AvatarFallback>
        </Avatar>

        <div className="min-w-0">
          <h3 className="font-semibold truncate">{threadInfo?.other_party_name || t('loading')}</h3>
          <p className="text-xs text-muted-foreground">{t('doctor')}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col">
        {currentThread?.has_more && (
          <div className="text-center">
            <Button variant="ghost" size="sm" onClick={handleLoadMore} disabled={isLoadingMessages}>
              {isLoadingMessages ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                t('loadMore') || 'Load more'
              )}
            </Button>
          </div>
        )}

        {isLoadingMessages && !currentThread?.messages.length && <ChatSkeleton />}

        {!isLoadingMessages && currentThread?.messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground p-8">
            <Stethoscope className="w-12 h-12 text-muted-foreground/30 mb-4" />
            <p className="text-sm">
              {t('noMessages') || 'No messages yet. Start the conversation!'}
            </p>
          </div>
        )}

        {currentThread?.messages && currentThread.messages.length > 0 && (
          <div className="space-y-4">
            {currentThread.messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isOwnMessage={message.sender_type === 'PATIENT'}
              />
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      {currentThread?.can_send_message ? (
        <MessageInput onSend={handleSendMessage} disabled={!currentThread?.can_send_message} />
      ) : (
        <div className="p-4 border-t border-border bg-muted/50 text-center">
          <p className="text-sm text-muted-foreground">{t('connectionRequired')}</p>
        </div>
      )}
    </div>
  )
}

// Main Page Component
export default function ConversationsPage() {
  const [activeTab, setActiveTab] = useState<'ai' | 'doctor'>('ai')
  const chatT = useTranslations('patient.chat')
  const messagingT = useTranslations('messaging')
  const t = useTranslations('patient.conversations')

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Tab Header */}
      <div className="p-3 border-b border-border bg-background">
        <SegmentedControl
          value={activeTab}
          onChange={setActiveTab}
          options={[
            { value: 'ai' as const, label: t('aiChat', { defaultValue: 'AI Support' }), icon: Bot },
            {
              value: 'doctor' as const,
              label: t('doctorMessages', { defaultValue: 'My Doctor' }),
              icon: Stethoscope,
            },
          ]}
        />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'ai' ? <AIChat t={chatT} /> : <DoctorMessages t={messagingT} />}
      </div>
    </div>
  )
}
