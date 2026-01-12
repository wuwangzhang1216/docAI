'use client';

import { useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ThreadListSkeleton } from '@/components/ui/skeleton';
import { SearchInput } from '@/components/ui/search-input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ThreadSummary } from '@/lib/messaging';
import { Image as ImageIcon, FileText, Loader2, MessageSquare } from 'lucide-react';

interface ThreadListProps {
  threads: ThreadSummary[];
  selectedThreadId?: string;
  onSelectThread: (threadId: string) => void;
  loading?: boolean;
  emptyStateAction?: React.ReactNode;
  // Pagination & search
  hasMore?: boolean;
  onLoadMore?: () => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  showSearch?: boolean;
}

export function ThreadList({
  threads,
  selectedThreadId,
  onSelectThread,
  loading = false,
  emptyStateAction,
  hasMore = false,
  onLoadMore,
  searchQuery = '',
  onSearchChange,
  showSearch = false,
}: ThreadListProps) {
  const t = useTranslations('messaging');
  const common = useTranslations('common');
  const [localSearch, setLocalSearch] = useState(searchQuery);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const handleSearchChange = useCallback((value: string) => {
    setLocalSearch(value);
    onSearchChange?.(value);
  }, [onSearchChange]);

  const handleLoadMore = useCallback(async () => {
    if (!onLoadMore || isLoadingMore) return;
    setIsLoadingMore(true);
    await onLoadMore();
    setIsLoadingMore(false);
  }, [onLoadMore, isLoadingMore]);

  const formatTime = (dateStr?: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return t('yesterday') || 'Yesterday';
    }

    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const getMessagePreview = (thread: ThreadSummary) => {
    if (!thread.last_message_preview) return null;

    if (thread.last_message_type === 'IMAGE') {
      return (
        <span className="flex items-center gap-1 text-muted-foreground">
          <ImageIcon className="w-3.5 h-3.5" />
          {t('fileTypes.image')}
        </span>
      );
    }

    if (thread.last_message_type === 'FILE') {
      return (
        <span className="flex items-center gap-1 text-muted-foreground">
          <FileText className="w-3.5 h-3.5" />
          {t('fileTypes.file')}
        </span>
      );
    }

    return thread.last_message_preview;
  };

  // Initial loading with no threads
  if (loading && threads.length === 0) {
    return (
      <div className="flex flex-col h-full">
        {showSearch && (
          <div className="p-3 border-b border-border">
            <SearchInput
              value={localSearch}
              onChange={handleSearchChange}
              placeholder={t('searchConversations')}
              disabled
            />
          </div>
        )}
        <div className="flex-1 p-4">
          <ThreadListSkeleton />
        </div>
      </div>
    );
  }

  // Empty state (no threads or no search results)
  if (threads.length === 0) {
    return (
      <div className="flex flex-col h-full">
        {showSearch && (
          <div className="p-3 border-b border-border">
            <SearchInput
              value={localSearch}
              onChange={handleSearchChange}
              placeholder={t('searchConversations')}
            />
          </div>
        )}
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
            <MessageSquare className="w-8 h-8 text-muted-foreground" />
          </div>
          {localSearch ? (
            <>
              <h3 className="text-lg font-semibold mb-2">{common('noResults')}</h3>
              <button
                onClick={() => handleSearchChange('')}
                className="text-sm text-primary hover:underline"
              >
                {common('clearFilters')}
              </button>
            </>
          ) : (
            <>
              <h3 className="text-lg font-semibold mb-2">{t('noConversations')}</h3>
              {emptyStateAction}
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search input */}
      {showSearch && (
        <div className="p-3 border-b border-border shrink-0">
          <SearchInput
            value={localSearch}
            onChange={handleSearchChange}
            placeholder={t('searchConversations')}
          />
        </div>
      )}

      {/* Thread list */}
      <div className="flex-1 overflow-y-auto">
        {threads.map((thread) => (
        <button
          key={thread.id}
          onClick={() => onSelectThread(thread.id)}
          className={cn(
            "w-full p-4 border-b border-border text-left flex items-center gap-3 transition-colors",
            selectedThreadId === thread.id
              ? "bg-primary/5"
              : "hover:bg-muted/50"
          )}
        >
          {/* Avatar */}
          <Avatar className="w-12 h-12 shrink-0">
            <AvatarFallback className={cn(
              thread.other_party_type === 'DOCTOR'
                ? "bg-blue-100 text-blue-600"
                : "bg-emerald-100 text-emerald-600"
            )}>
              {thread.other_party_name.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <span className={cn(
                "font-medium truncate",
                thread.unread_count > 0 && "font-semibold"
              )}>
                {thread.other_party_name}
              </span>
              <span className="text-xs text-muted-foreground shrink-0">
                {formatTime(thread.last_message_at)}
              </span>
            </div>

            <div className="flex items-center justify-between gap-2 mt-0.5">
              <p className={cn(
                "text-sm truncate",
                thread.unread_count > 0
                  ? "text-foreground font-medium"
                  : "text-muted-foreground"
              )}>
                {getMessagePreview(thread)}
              </p>

              {/* Unread badge */}
              {thread.unread_count > 0 && (
                <span className="bg-primary text-primary-foreground text-xs font-medium rounded-full px-2 py-0.5 shrink-0">
                  {thread.unread_count > 99 ? '99+' : thread.unread_count}
                </span>
              )}
            </div>

            {/* Connection status */}
            {!thread.can_send_message && (
              <p className="text-xs text-amber-600 mt-1">
                {t('connectionRequired')}
              </p>
            )}
          </div>
        </button>
        ))}

        {/* Load more button */}
        {hasMore && onLoadMore && (
          <div className="p-4 text-center">
            <Button
              variant="outline"
              size="sm"
              onClick={handleLoadMore}
              disabled={isLoadingMore}
              className="w-full"
            >
              {isLoadingMore ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {common('loading')}
                </>
              ) : (
                t('loadMore')
              )}
            </Button>
          </div>
        )}

        {/* Loading overlay for pagination */}
        {loading && threads.length > 0 && (
          <div className="p-4 text-center">
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-primary" />
          </div>
        )}
      </div>
    </div>
  );
}
