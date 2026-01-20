'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { Send, UserCheck, ArrowLeft, Loader2, Bot, Stethoscope } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from '@/components/ui/dialog';
import { ThreadList, MessageBubble, MessageInput } from '@/components/messaging';
import { ChatSkeleton } from '@/components/ui/skeleton';
import { useMessagingStore, type MessageType } from '@/lib/messaging';
import { useWebSocket, type WSMessage } from '@/hooks/useWebSocket';
import { cn } from '@/lib/utils';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface DoctorInfo {
  id: string;
  full_name: string;
  specialty?: string;
}

// Tab button component
function TabButton({
  active,
  onClick,
  children,
  icon: Icon,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  icon: React.ElementType;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex-1 flex items-center justify-center gap-2 py-2.5 px-4 text-sm font-medium rounded-lg transition-all",
        active
          ? "bg-primary text-primary-foreground"
          : "bg-muted text-muted-foreground hover:text-foreground"
      )}
    >
      <Icon className="w-4 h-4" />
      {children}
    </button>
  );
}

// AI Chat Component
function AIChat({ t }: { t: ReturnType<typeof useTranslations<'patient.chat'>> }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [showCrisisModal, setShowCrisisModal] = useState(false);
  const [connectedDoctor, setConnectedDoctor] = useState<DoctorInfo | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const checkConnectedDoctor = async () => {
      try {
        const doctor = await api.getMyDoctor();
        setConnectedDoctor(doctor);
      } catch {
        setConnectedDoctor(null);
      }
    };
    checkConnectedDoctor();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await api.sendMessage(userMessage, conversationId || undefined);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: res.reply },
      ]);
      setConversationId(res.conversation_id);

      if (res.risk_alert) {
        setShowCrisisModal(true);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: t('errorMessage') },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col min-h-full p-4 space-y-6">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground p-8">
              <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-4">
                <span className="text-3xl">👋</span>
              </div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">{t('welcomeTitle')}</h3>
              <p className="max-w-xs text-sm">{t('welcomeMessage')}</p>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse animate-message-right' : 'flex-row animate-message-left'}`}
                >
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className={msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}>
                      {msg.role === 'user' ? 'ME' : 'AI'}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${msg.role === 'user'
                      ? 'bg-primary text-primary-foreground rounded-tr-sm'
                      : 'bg-card text-card-foreground border border-border rounded-tl-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex gap-3 animate-message-left">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-muted">AI</AvatarFallback>
                  </Avatar>
                  <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex items-center space-x-1">
                    <div className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                    <div className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="bg-background/80 backdrop-blur-md p-4 pb-2 border-t border-border">
        <form
          className="flex items-end space-x-2 max-w-2xl mx-auto"
          onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('placeholder')}
            className="rounded-full pl-6 pr-6 py-6 border-0 bg-muted/50 focus-visible:ring-1 focus-visible:bg-background shadow-inner resize-none"
            disabled={loading}
          />
          <Button
            type="submit"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            size="icon"
            className="h-12 w-12 rounded-full shrink-0 shadow-sm"
          >
            <Send className="w-5 h-5 ml-0.5" />
          </Button>
        </form>
        <p className="text-xs text-muted-foreground text-center mt-2 max-w-2xl mx-auto">
          {t('disclaimer')}
        </p>
      </div>

      {/* Crisis Modal */}
      <Dialog open={showCrisisModal} onClose={() => setShowCrisisModal(false)}>
        <DialogBackdrop />
        <DialogPanel>
          <DialogTitle className="text-destructive flex items-center">
            <span className="mr-2">🚨</span> {t('crisisTitle')}
          </DialogTitle>
          <p className="text-muted-foreground mb-4 text-sm leading-relaxed">
            {t('crisisMessage')}
          </p>
          <ul className="space-y-2 mb-4 text-sm font-medium bg-muted/50 p-4 rounded-lg">
            <li className="flex items-center text-foreground"><span className="w-1.5 h-1.5 rounded-full bg-destructive mr-2" />{t('crisisLine1')}</li>
            <li className="flex items-center text-foreground"><span className="w-1.5 h-1.5 rounded-full bg-destructive mr-2" />{t('crisisLine2')}</li>
          </ul>
          {connectedDoctor && (
            <div className="mb-4 p-3 bg-primary/10 rounded-lg flex items-center gap-2 text-sm">
              <UserCheck className="w-4 h-4 text-primary shrink-0" />
              <span className="text-foreground">
                {t('doctorNotified', {
                  doctorName: connectedDoctor.full_name,
                  defaultValue: `Dr. ${connectedDoctor.full_name} has been notified and will follow up with you.`
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
  );
}

// Doctor Messages Component
function DoctorMessages({ t }: { t: ReturnType<typeof useTranslations<'messaging'>> }) {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
  } = useMessagingStore();

  const handleWSMessage = useCallback((message: WSMessage) => {
    if (message.type === 'new_message' && message.payload) {
      handleNewMessage(message.payload as unknown as Parameters<typeof handleNewMessage>[0]);
    } else if (message.type === 'message_read' && message.payload) {
      const payload = message.payload as unknown as { thread_id: string; reader_type: 'DOCTOR' | 'PATIENT' };
      handleMessageRead(payload.thread_id, payload.reader_type);
    }
  }, [handleNewMessage, handleMessageRead]);

  const { subscribeToThread, unsubscribeFromThread } = useWebSocket({
    onMessage: handleWSMessage,
    autoConnect: true,
  });

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  useEffect(() => {
    if (selectedThreadId) {
      loadThread(selectedThreadId);
      subscribeToThread(selectedThreadId);
      markAsRead(selectedThreadId);
    }

    return () => {
      if (selectedThreadId) {
        unsubscribeFromThread(selectedThreadId);
      }
    };
  }, [selectedThreadId, loadThread, subscribeToThread, unsubscribeFromThread, markAsRead]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentThread?.messages]);

  const handleSelectThread = (threadId: string) => {
    setSelectedThreadId(threadId);
  };

  const handleBack = () => {
    setSelectedThreadId(null);
    clearCurrentThread();
  };

  const handleSendMessage = async (
    content: string,
    messageType: MessageType,
    attachmentIds?: string[]
  ) => {
    if (!selectedThreadId) return;
    await sendMessage(selectedThreadId, content, messageType, attachmentIds);
  };

  const handleLoadMore = () => {
    if (selectedThreadId && currentThread?.has_more) {
      loadThread(selectedThreadId, true);
    }
  };

  if (!selectedThreadId) {
    return (
      <div className="flex flex-col h-full">
        <ThreadList
          threads={threads}
          onSelectThread={handleSelectThread}
          loading={isLoadingThreads}
        />
      </div>
    );
  }

  const threadInfo = currentThread || threads.find((th) => th.id === selectedThreadId);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border bg-background flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleBack}
          className="shrink-0"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>

        <Avatar className="w-10 h-10 shrink-0">
          <AvatarFallback className="bg-blue-100 text-blue-600">
            {threadInfo?.other_party_name?.charAt(0).toUpperCase() || 'D'}
          </AvatarFallback>
        </Avatar>

        <div className="min-w-0">
          <h3 className="font-semibold truncate">
            {threadInfo?.other_party_name || t('loading')}
          </h3>
          <p className="text-xs text-muted-foreground">{t('doctor')}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col">
        {currentThread?.has_more && (
          <div className="text-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLoadMore}
              disabled={isLoadingMessages}
            >
              {isLoadingMessages ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                t('loadMore') || 'Load more'
              )}
            </Button>
          </div>
        )}

        {isLoadingMessages && !currentThread?.messages.length && (
          <ChatSkeleton />
        )}

        {!isLoadingMessages && currentThread?.messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground p-8">
            <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-4">
              <span className="text-3xl">👋</span>
            </div>
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
        <MessageInput
          onSend={handleSendMessage}
          disabled={!currentThread?.can_send_message}
        />
      ) : (
        <div className="p-4 border-t border-border bg-muted/50 text-center">
          <p className="text-sm text-muted-foreground">
            {t('connectionRequired')}
          </p>
        </div>
      )}
    </div>
  );
}

// Main Page Component
export default function ConversationsPage() {
  const [activeTab, setActiveTab] = useState<'ai' | 'doctor'>('ai');
  const chatT = useTranslations('patient.chat');
  const messagingT = useTranslations('messaging');
  const t = useTranslations('patient.conversations');

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Tab Header */}
      <div className="p-3 border-b border-border bg-background">
        <div className="flex gap-2 p-1 bg-muted rounded-xl">
          <TabButton
            active={activeTab === 'ai'}
            onClick={() => setActiveTab('ai')}
            icon={Bot}
          >
            {t('aiChat', { defaultValue: 'AI Support' })}
          </TabButton>
          <TabButton
            active={activeTab === 'doctor'}
            onClick={() => setActiveTab('doctor')}
            icon={Stethoscope}
          >
            {t('doctorMessages', { defaultValue: 'My Doctor' })}
          </TabButton>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'ai' ? (
          <AIChat t={chatT} />
        ) : (
          <DoctorMessages t={messagingT} />
        )}
      </div>
    </div>
  );
}
