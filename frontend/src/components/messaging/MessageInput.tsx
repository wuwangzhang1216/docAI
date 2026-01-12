'use client';

import { useState, useRef, useCallback } from 'react';
import { Send, Paperclip, Image as ImageIcon, X, Loader2 } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import type { UploadedAttachment, MessageType } from '@/lib/messaging';

interface MessageInputProps {
  onSend: (content: string, messageType: MessageType, attachmentIds?: string[]) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const ALLOWED_FILE_TYPES = [
  ...ALLOWED_IMAGE_TYPES,
  'application/pdf',
  'text/plain',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

export function MessageInput({ onSend, disabled = false, placeholder }: MessageInputProps) {
  const t = useTranslations('messaging');
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<UploadedAttachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback(async (files: FileList | null, isImage = false) => {
    if (!files || files.length === 0) return;

    setError(null);
    setIsUploading(true);

    try {
      for (const file of Array.from(files)) {
        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
          setError(t('errors.fileTooLarge'));
          continue;
        }

        // Validate file type
        const allowedTypes = isImage ? ALLOWED_IMAGE_TYPES : ALLOWED_FILE_TYPES;
        if (!allowedTypes.includes(file.type)) {
          setError(t('errors.unsupportedType'));
          continue;
        }

        // Upload file
        const uploaded = await api.uploadAttachment(file);

        // Create preview URL for images
        const previewUrl = file.type.startsWith('image/')
          ? URL.createObjectURL(file)
          : undefined;

        setAttachments((prev) => [
          ...prev,
          {
            ...uploaded,
            preview_url: previewUrl,
          },
        ]);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      setError(t('errors.sendFailed'));
    } finally {
      setIsUploading(false);
    }
  }, [t]);

  const removeAttachment = useCallback((id: string) => {
    setAttachments((prev) => {
      const att = prev.find((a) => a.id === id);
      if (att?.preview_url) {
        URL.revokeObjectURL(att.preview_url);
      }
      return prev.filter((a) => a.id !== id);
    });
  }, []);

  const handleSend = async () => {
    const content = input.trim();
    if (!content && attachments.length === 0) return;
    if (isSending) return;

    setIsSending(true);
    setError(null);

    try {
      // Determine message type
      let messageType: MessageType = 'TEXT';
      if (attachments.length > 0) {
        const hasImage = attachments.some((a) => a.file_type.startsWith('image/'));
        messageType = hasImage ? 'IMAGE' : 'FILE';
      }

      const attachmentIds = attachments.map((a) => a.id);
      await onSend(content, messageType, attachmentIds.length > 0 ? attachmentIds : undefined);

      // Clear input and attachments on success
      setInput('');
      attachments.forEach((a) => {
        if (a.preview_url) URL.revokeObjectURL(a.preview_url);
      });
      setAttachments([]);
    } catch (err) {
      console.error('Send failed:', err);
      setError(t('errors.sendFailed'));
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border bg-background">
      {/* Error message */}
      {error && (
        <div className="px-4 py-2 bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      )}

      {/* Attachment previews */}
      {attachments.length > 0 && (
        <div className="px-4 py-2 flex gap-2 overflow-x-auto border-b border-border">
          {attachments.map((att) => (
            <div
              key={att.id}
              className="relative flex-shrink-0 group"
            >
              {att.file_type.startsWith('image/') ? (
                <div className="w-16 h-16 rounded-lg overflow-hidden bg-muted">
                  <img
                    src={att.preview_url || ''}
                    alt={att.file_name}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-lg bg-muted flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-xs font-medium truncate max-w-[60px]">
                      {att.file_name.split('.').pop()?.toUpperCase()}
                    </div>
                  </div>
                </div>
              )}

              {/* Remove button */}
              <button
                onClick={() => removeAttachment(att.id)}
                className="absolute -top-1 -right-1 w-5 h-5 bg-destructive text-destructive-foreground rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}

          {isUploading && (
            <div className="w-16 h-16 rounded-lg bg-muted flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          )}
        </div>
      )}

      {/* Input area */}
      <div className="p-4 flex items-end gap-2">
        {/* Attachment buttons */}
        <div className="flex gap-1">
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_FILE_TYPES.join(',')}
            multiple
            className="hidden"
            onChange={(e) => handleFileSelect(e.target.files)}
            disabled={disabled || isUploading}
          />
          <input
            ref={imageInputRef}
            type="file"
            accept={ALLOWED_IMAGE_TYPES.join(',')}
            multiple
            className="hidden"
            onChange={(e) => handleFileSelect(e.target.files, true)}
            disabled={disabled || isUploading}
          />

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => imageInputRef.current?.click()}
            disabled={disabled || isUploading}
            className="text-muted-foreground hover:text-foreground"
          >
            <ImageIcon className="w-5 h-5" />
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isUploading}
            className="text-muted-foreground hover:text-foreground"
          >
            <Paperclip className="w-5 h-5" />
          </Button>
        </div>

        {/* Text input */}
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || t('placeholder')}
          className="flex-1 rounded-full"
          disabled={disabled || isSending}
        />

        {/* Send button */}
        <Button
          onClick={handleSend}
          disabled={disabled || isSending || (!input.trim() && attachments.length === 0)}
          size="icon"
          className="rounded-full shrink-0"
        >
          {isSending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </Button>
      </div>
    </div>
  );
}
