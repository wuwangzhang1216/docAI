'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ThreadList, MessageBubble, MessageInput } from '@/components/messaging';
import { ChatSkeleton } from '@/components/ui/skeleton';
import { useMessagingStore, type MessageType } from '@/lib/messaging';
import { useWebSocket, type WSMessage } from '@/hooks/useWebSocket';
import { cn } from '@/lib/utils';

export default function PatientMessagesPage() {
  const t = useTranslations('messaging');
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

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

  // WebSocket connection
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

  // Load threads on mount
  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  // Load thread when selected
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

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentThread?.messages]);

  // Handle thread selection
  const handleSelectThread = (threadId: string) => {
    setSelectedThreadId(threadId);
  };

  // Handle back button
  const handleBack = () => {
    setSelectedThreadId(null);
    clearCurrentThread();
  };

  // Handle send message
  const handleSendMessage = async (
    content: string,
    messageType: MessageType,
    attachmentIds?: string[]
  ) => {
    if (!selectedThreadId) return;
    await sendMessage(selectedThreadId, content, messageType, attachmentIds);
  };

  // Handle load more messages
  const handleLoadMore = () => {
    if (selectedThreadId && currentThread?.has_more) {
      loadThread(selectedThreadId, true);
    }
  };

  // Thread list view
  if (!selectedThreadId) {
    return (
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-border bg-background">
          <h2 className="text-lg font-semibold">{t('title')}</h2>
        </div>

        {/* Thread list */}
        <ThreadList
          threads={threads}
          onSelectThread={handleSelectThread}
          loading={isLoadingThreads}
        />
      </div>
    );
  }

  // Get current thread from store or threads list
  const threadInfo = currentThread || threads.find((t) => t.id === selectedThreadId);

  // Conversation view
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
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 flex flex-col"
      >
        {/* Load more button */}
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

        {/* Loading */}
        {isLoadingMessages && !currentThread?.messages.length && (
          <ChatSkeleton />
        )}

        {/* Empty state */}
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

        {/* Messages */}
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
