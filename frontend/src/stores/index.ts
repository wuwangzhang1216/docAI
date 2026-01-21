/**
 * Centralized exports for all Zustand stores.
 */

// Auth store
export { useAuth, getRedirectPath, isRouteAllowed } from './auth.store';
export type { UserType } from './auth.store';

// i18n store
export { useI18n } from './i18n.store';
export type { Locale } from './i18n.store';

// Messaging store
export { useMessagingStore } from './messaging.store';
export type {
  MessageType,
  Attachment,
  Message,
  ThreadSummary,
  ThreadDetail,
  UnreadCount,
  UploadedAttachment,
} from './messaging.store';
