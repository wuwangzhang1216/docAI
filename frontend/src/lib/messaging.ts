'use client';

import { create } from 'zustand';
import { api } from './api';

// Types
export type MessageType = 'TEXT' | 'IMAGE' | 'FILE';

export interface Attachment {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  url: string;
  thumbnail_url?: string;
}

export interface Message {
  id: string;
  thread_id: string;
  sender_type: 'DOCTOR' | 'PATIENT';
  sender_id: string;
  sender_name: string;
  content?: string;
  message_type: MessageType;
  is_read: boolean;
  read_at?: string;
  created_at: string;
  attachments: Attachment[];
}

export interface ThreadSummary {
  id: string;
  other_party_id: string;
  other_party_name: string;
  other_party_type: 'DOCTOR' | 'PATIENT';
  last_message_preview?: string;
  last_message_at?: string;
  last_message_type?: MessageType;
  unread_count: number;
  can_send_message: boolean;
  created_at: string;
}

export interface ThreadDetail {
  id: string;
  other_party_id: string;
  other_party_name: string;
  other_party_type: 'DOCTOR' | 'PATIENT';
  can_send_message: boolean;
  messages: Message[];
  has_more: boolean;
  created_at: string;
}

export interface UnreadCount {
  total_unread: number;
  threads: { thread_id: string; unread_count: number }[];
}

export interface UploadedAttachment {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  s3_key: string;
  thumbnail_s3_key?: string;
  // Local preview
  preview_url?: string;
}

interface MessagingState {
  // Data
  threads: ThreadSummary[];
  currentThread: ThreadDetail | null;
  totalUnread: number;

  // Pagination & search
  totalThreads: number;
  threadsHasMore: boolean;
  searchQuery: string;

  // Loading states
  isLoadingThreads: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;

  // Actions
  loadThreads: (options?: { search?: string; append?: boolean }) => Promise<void>;
  loadThread: (threadId: string, append?: boolean) => Promise<void>;
  sendMessage: (
    threadId: string,
    content: string,
    messageType?: MessageType,
    attachmentIds?: string[]
  ) => Promise<Message | null>;
  markAsRead: (threadId: string) => Promise<void>;
  loadUnreadCount: () => Promise<void>;
  startThreadWithPatient: (patientId: string) => Promise<ThreadSummary | null>;
  setSearchQuery: (query: string) => void;

  // WebSocket handlers
  handleNewMessage: (message: Message) => void;
  handleMessageRead: (threadId: string, readerType: 'DOCTOR' | 'PATIENT') => void;
  handleUnreadUpdate: (total: number) => void;

  // Utility
  clearCurrentThread: () => void;
  reset: () => void;
}

const THREADS_PAGE_SIZE = 20;

export const useMessagingStore = create<MessagingState>((set, get) => ({
  // Initial state
  threads: [],
  currentThread: null,
  totalUnread: 0,
  totalThreads: 0,
  threadsHasMore: false,
  searchQuery: '',
  isLoadingThreads: false,
  isLoadingMessages: false,
  isSending: false,

  // Load threads with optional search and pagination
  loadThreads: async (options?: { search?: string; append?: boolean }) => {
    const { threads: currentThreads, searchQuery: currentSearch } = get();
    const search = options?.search ?? currentSearch;
    const append = options?.append ?? false;

    set({ isLoadingThreads: true });
    try {
      const response = await api.getThreads({
        limit: THREADS_PAGE_SIZE,
        offset: append ? currentThreads.length : 0,
        search: search || undefined,
      });

      if (append) {
        set({
          threads: [...currentThreads, ...response.items],
          totalThreads: response.total,
          threadsHasMore: response.has_more,
          isLoadingThreads: false,
        });
      } else {
        set({
          threads: response.items,
          totalThreads: response.total,
          threadsHasMore: response.has_more,
          searchQuery: search,
          isLoadingThreads: false,
        });
      }
    } catch (error) {
      console.error('Failed to load threads:', error);
      set({ isLoadingThreads: false });
    }
  },

  // Set search query and reload threads
  setSearchQuery: (query: string) => {
    set({ searchQuery: query });
    get().loadThreads({ search: query });
  },

  // Load thread with messages
  loadThread: async (threadId: string, append = false) => {
    const { currentThread } = get();

    // If appending (loading more), use the oldest message timestamp
    const before = append && currentThread?.messages.length
      ? currentThread.messages[0].created_at
      : undefined;

    set({ isLoadingMessages: true });
    try {
      const thread = await api.getThread(threadId, 50, before);

      if (append && currentThread) {
        // Prepend older messages
        set({
          currentThread: {
            ...thread,
            messages: [...thread.messages, ...currentThread.messages],
          },
          isLoadingMessages: false,
        });
      } else {
        set({ currentThread: thread, isLoadingMessages: false });
      }

      // Update unread count in threads list
      set((state) => ({
        threads: state.threads.map((t) =>
          t.id === threadId ? { ...t, unread_count: 0 } : t
        ),
      }));
    } catch (error) {
      console.error('Failed to load thread:', error);
      set({ isLoadingMessages: false });
    }
  },

  // Send a message
  sendMessage: async (
    threadId: string,
    content: string,
    messageType: MessageType = 'TEXT',
    attachmentIds?: string[]
  ) => {
    set({ isSending: true });
    try {
      const message = await api.sendDirectMessage(threadId, content, messageType, attachmentIds);

      // Add message to current thread if viewing
      const { currentThread } = get();
      if (currentThread?.id === threadId) {
        set({
          currentThread: {
            ...currentThread,
            messages: [...currentThread.messages, message],
          },
        });
      }

      // Update thread in list
      set((state) => ({
        threads: state.threads.map((t) =>
          t.id === threadId
            ? {
                ...t,
                last_message_preview: content || `[${messageType}]`,
                last_message_at: message.created_at,
                last_message_type: messageType,
              }
            : t
        ),
      }));

      set({ isSending: false });
      return message;
    } catch (error) {
      console.error('Failed to send message:', error);
      set({ isSending: false });
      return null;
    }
  },

  // Mark thread as read
  markAsRead: async (threadId: string) => {
    try {
      await api.markThreadAsRead(threadId);

      // Update local state
      set((state) => {
        const thread = state.threads.find((t) => t.id === threadId);
        const unreadDiff = thread?.unread_count || 0;

        return {
          threads: state.threads.map((t) =>
            t.id === threadId ? { ...t, unread_count: 0 } : t
          ),
          totalUnread: Math.max(0, state.totalUnread - unreadDiff),
        };
      });
    } catch (error) {
      console.error('Failed to mark thread as read:', error);
    }
  },

  // Load unread count
  loadUnreadCount: async () => {
    try {
      const unread = await api.getUnreadCount();
      set({ totalUnread: unread.total_unread });
    } catch (error) {
      console.error('Failed to load unread count:', error);
    }
  },

  // Start thread with patient (doctor only)
  startThreadWithPatient: async (patientId: string) => {
    try {
      const thread = await api.startThreadWithPatient(patientId);

      // Add to threads list if not exists
      set((state) => {
        const exists = state.threads.some((t) => t.id === thread.id);
        if (!exists) {
          return { threads: [thread, ...state.threads] };
        }
        return state;
      });

      return thread;
    } catch (error) {
      console.error('Failed to start thread:', error);
      return null;
    }
  },

  // Handle new message from WebSocket
  handleNewMessage: (message: Message) => {
    const { currentThread } = get();

    // Add to current thread if viewing
    if (currentThread?.id === message.thread_id) {
      // Check if message already exists (prevent duplicates)
      const exists = currentThread.messages.some((m) => m.id === message.id);
      if (!exists) {
        set({
          currentThread: {
            ...currentThread,
            messages: [...currentThread.messages, message],
          },
        });
      }
    }

    // Update threads list
    set((state) => {
      const threadIndex = state.threads.findIndex((t) => t.id === message.thread_id);

      if (threadIndex === -1) {
        // Thread not in list, reload threads
        get().loadThreads();
        return state;
      }

      const updatedThreads = [...state.threads];
      const thread = updatedThreads[threadIndex];

      // Update thread info
      updatedThreads[threadIndex] = {
        ...thread,
        last_message_preview: message.content || `[${message.message_type}]`,
        last_message_at: message.created_at,
        last_message_type: message.message_type,
        unread_count: currentThread?.id === message.thread_id ? 0 : thread.unread_count + 1,
      };

      // Move thread to top
      const [updatedThread] = updatedThreads.splice(threadIndex, 1);
      updatedThreads.unshift(updatedThread);

      // Update total unread if not viewing this thread
      const newTotalUnread =
        currentThread?.id === message.thread_id
          ? state.totalUnread
          : state.totalUnread + 1;

      return {
        threads: updatedThreads,
        totalUnread: newTotalUnread,
      };
    });
  },

  // Handle message read from WebSocket
  handleMessageRead: (threadId: string, readerType: 'DOCTOR' | 'PATIENT') => {
    const { currentThread } = get();

    // Update messages in current thread
    if (currentThread?.id === threadId) {
      set({
        currentThread: {
          ...currentThread,
          messages: currentThread.messages.map((m) =>
            m.sender_type !== readerType && !m.is_read
              ? { ...m, is_read: true, read_at: new Date().toISOString() }
              : m
          ),
        },
      });
    }
  },

  // Handle unread update from WebSocket
  handleUnreadUpdate: (total: number) => {
    set({ totalUnread: total });
  },

  // Clear current thread
  clearCurrentThread: () => {
    set({ currentThread: null });
  },

  // Reset store
  reset: () => {
    set({
      threads: [],
      currentThread: null,
      totalUnread: 0,
      totalThreads: 0,
      threadsHasMore: false,
      searchQuery: '',
      isLoadingThreads: false,
      isLoadingMessages: false,
      isSending: false,
    });
  },
}));
