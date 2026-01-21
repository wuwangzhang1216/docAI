/**
 * @deprecated Import from '@/stores' instead.
 * This file is kept for backward compatibility.
 */

'use client';

export { useMessagingStore } from '@/stores/messaging.store';
export type {
  MessageType,
  Attachment,
  Message,
  ThreadSummary,
  ThreadDetail,
  UnreadCount,
  UploadedAttachment,
} from '@/stores/messaging.store';
