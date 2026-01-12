'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { ArrowLeftIcon, Loader2Icon, UsersIcon } from '@/components/ui/icons';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ThreadList, MessageBubble, MessageInput } from '@/components/messaging';
import { useMessagingStore, type MessageType } from '@/lib/messaging';
import { useWebSocket, type WSMessage } from '@/hooks/useWebSocket';

export default function DoctorMessagesPage() {
  const t = useTranslations('messaging');
  const searchParams = useSearchParams();
  const patientIdFromUrl = searchParams.get('patient');

  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [hasProcessedPatientId, setHasProcessedPatientId] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    threads,
    currentThread,
    isLoadingThreads,
    isLoadingMessages,
    threadsHasMore,
    searchQuery,
    loadThreads,
    loadThread,
    sendMessage,
    markAsRead,
    startThreadWithPatient,
    setSearchQuery,
    handleNewMessage,
    handleMessageRead,
    clearCurrentThread,
  } = useMessagingStore();

  // WebSocket connection
  const handleWSMessage = useCallback((message: WSMessage) => {
    if (message.type === 'new_message' && message.payload) {
      handleNewMessage(message.payload as Parameters<typeof handleNewMessage>[0]);
    } else if (message.type === 'message_read' && message.payload) {
      const payload = message.payload as { thread_id: string; reader_type: 'DOCTOR' | 'PATIENT' };
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

  // Handle patient ID from URL (when navigating from patient list)
  useEffect(() => {
    const initFromPatientId = async () => {
      // Only process once and only after threads have finished loading
      if (!patientIdFromUrl || hasProcessedPatientId || isLoadingThreads) {
        return;
      }

      setHasProcessedPatientId(true);

      // Check if thread exists for this patient
      const existingThread = threads.find(
        (t) => t.other_party_id === patientIdFromUrl
      );

      if (existingThread) {
        setSelectedThreadId(existingThread.id);
      } else {
        // Start a new thread with this patient
        const newThread = await startThreadWithPatient(patientIdFromUrl);
        if (newThread) {
          setSelectedThreadId(newThread.id);
        }
      }
    };

    initFromPatientId();
  }, [patientIdFromUrl, threads, isLoadingThreads, hasProcessedPatientId, startThreadWithPatient]);

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
    if (currentThread?.messages && currentThread.messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
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

  // Handle load more threads
  const handleLoadMoreThreads = useCallback(() => {
    if (threadsHasMore) {
      loadThreads({ append: true });
    }
  }, [threadsHasMore, loadThreads]);

  // Thread list view
  if (!selectedThreadId) {
    return (
      <div className="flex flex-col h-full min-h-[600px] bg-background">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold">{t('title')}</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {t('doctorSubtitle') || 'Chat with your patients'}
          </p>
        </div>

        {/* Thread list */}
        <ThreadList
          threads={threads}
          onSelectThread={handleSelectThread}
          loading={isLoadingThreads}
          showSearch={true}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          hasMore={threadsHasMore}
          onLoadMore={handleLoadMoreThreads}
          emptyStateAction={
            <div className="mt-4">
              <p className="text-sm text-muted-foreground mb-3">
                {t('startFromPatientList', { defaultValue: 'Start a conversation from your patient list' })}
              </p>
              <Link
                href="/patients"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium text-sm"
              >
                <UsersIcon className="w-4 h-4" />
                {t('goToPatients', { defaultValue: 'Go to Patients' })}
              </Link>
            </div>
          }
        />
      </div>
    );
  }

  // Get current thread info
  const threadInfo = currentThread || threads.find((t) => t.id === selectedThreadId);

  // Conversation view
  return (
    <div className="flex flex-col h-full min-h-[600px] bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleBack}
          className="shrink-0"
        >
          <ArrowLeftIcon className="w-5 h-5" />
        </Button>

        <Avatar className="w-10 h-10 shrink-0">
          <AvatarFallback className="bg-emerald-100 text-emerald-600">
            {threadInfo?.other_party_name?.charAt(0).toUpperCase() || 'P'}
          </AvatarFallback>
        </Avatar>

        <div className="min-w-0">
          <h3 className="font-semibold truncate">
            {threadInfo?.other_party_name || t('loading')}
          </h3>
          <p className="text-xs text-muted-foreground">{t('patient')}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col">
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
                <Loader2Icon className="w-4 h-4 animate-spin" />
              ) : (
                t('loadMore') || 'Load more'
              )}
            </Button>
          </div>
        )}

        {/* Loading */}
        {isLoadingMessages && !currentThread?.messages.length && (
          <div className="flex-1 flex items-center justify-center">
            <Loader2Icon className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Empty state */}
        {!isLoadingMessages && currentThread?.messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground p-8">
            <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-4">
              <span className="text-3xl">💬</span>
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
                isOwnMessage={message.sender_type === 'DOCTOR'}
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
