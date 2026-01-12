'use client';

import { useState } from 'react';
import { Check, CheckCheck, Download, FileText, Image as ImageIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Message, Attachment } from '@/lib/messaging';
import { ImageViewer } from './ImageViewer';

interface MessageBubbleProps {
  message: Message;
  isOwnMessage: boolean;
  showSenderName?: boolean;
}

export function MessageBubble({ message, isOwnMessage, showSenderName = false }: MessageBubbleProps) {
  const [viewingImage, setViewingImage] = useState<string | null>(null);

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const renderAttachment = (attachment: Attachment) => {
    const isImage = attachment.file_type.startsWith('image/');

    if (isImage) {
      return (
        <button
          key={attachment.id}
          onClick={() => setViewingImage(attachment.url)}
          className="block overflow-hidden rounded-lg max-w-[240px] hover:opacity-90 transition-opacity"
        >
          <img
            src={attachment.thumbnail_url || attachment.url}
            alt={attachment.file_name}
            className="w-full h-auto object-cover"
            loading="lazy"
          />
        </button>
      );
    }

    // File attachment
    return (
      <a
        key={attachment.id}
        href={attachment.url}
        target="_blank"
        rel="noopener noreferrer"
        download={attachment.file_name}
        className={cn(
          "flex items-center gap-3 p-3 rounded-lg border transition-colors",
          isOwnMessage
            ? "bg-primary-foreground/10 border-primary-foreground/20 hover:bg-primary-foreground/20"
            : "bg-muted/50 border-border hover:bg-muted"
        )}
      >
        <div className={cn(
          "w-10 h-10 rounded-lg flex items-center justify-center",
          isOwnMessage ? "bg-primary-foreground/20" : "bg-muted"
        )}>
          <FileText className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{attachment.file_name}</p>
          <p className={cn(
            "text-xs",
            isOwnMessage ? "text-primary-foreground/70" : "text-muted-foreground"
          )}>
            {formatFileSize(attachment.file_size)}
          </p>
        </div>
        <Download className="w-4 h-4 opacity-60" />
      </a>
    );
  };

  return (
    <>
      <div
        className={cn(
          "flex gap-2 max-w-[85%]",
          isOwnMessage ? "ml-auto flex-row-reverse" : "mr-auto"
        )}
      >
        <div className="flex flex-col gap-1">
          {/* Sender name */}
          {showSenderName && !isOwnMessage && (
            <span className="text-xs text-muted-foreground px-1">
              {message.sender_name}
            </span>
          )}

          {/* Message content */}
          <div
            className={cn(
              "rounded-2xl px-4 py-2.5",
              isOwnMessage
                ? "bg-primary text-primary-foreground rounded-tr-sm"
                : "bg-card border border-border rounded-tl-sm"
            )}
          >
            {/* Attachments */}
            {message.attachments.length > 0 && (
              <div className="flex flex-col gap-2 mb-2">
                {message.attachments.map(renderAttachment)}
              </div>
            )}

            {/* Text content */}
            {message.content && (
              <p className="text-sm whitespace-pre-wrap break-words">
                {message.content}
              </p>
            )}

            {/* Time and read status */}
            <div className={cn(
              "flex items-center gap-1 mt-1",
              isOwnMessage ? "justify-end" : "justify-start"
            )}>
              <span className={cn(
                "text-[10px]",
                isOwnMessage ? "text-primary-foreground/70" : "text-muted-foreground"
              )}>
                {formatTime(message.created_at)}
              </span>

              {/* Read status (only for own messages) */}
              {isOwnMessage && (
                <span className={cn(
                  "text-primary-foreground/70",
                  message.is_read && "text-blue-300"
                )}>
                  {message.is_read ? (
                    <CheckCheck className="w-3.5 h-3.5" />
                  ) : (
                    <Check className="w-3.5 h-3.5" />
                  )}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Image viewer modal */}
      {viewingImage && (
        <ImageViewer
          src={viewingImage}
          onClose={() => setViewingImage(null)}
        />
      )}
    </>
  );
}
