'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { Send, UserCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from '@/components/ui/dialog';
import { StreamingMessage, ErrorMessage } from '@/components/chat/StreamingMessage';

interface ToolCall {
  id: string;
  name: string;
  status: 'running' | 'completed';
  resultPreview?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
  error?: string;
}

interface DoctorInfo {
  id: string;
  full_name: string;
  specialty?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [showCrisisModal, setShowCrisisModal] = useState(false);
  const [connectedDoctor, setConnectedDoctor] = useState<DoctorInfo | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const t = useTranslations('patient.chat');

  // Check if user has a connected doctor
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

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setLoading(true);

    // Add user message and placeholder assistant message
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userMessage },
      { role: 'assistant', content: '', isStreaming: true, toolCalls: [] },
    ]);

    // Index of the assistant message we're updating
    const assistantIndex = messages.length + 1;

    try {
      await api.sendMessageStream(
        userMessage,
        conversationId || undefined,
        {
          onRiskCheck: (level, riskType) => {
            console.log('Risk check:', level, riskType);
          },

          onToolStart: (toolId, toolName) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMsg = newMessages[assistantIndex];
              if (lastMsg?.role === 'assistant') {
                lastMsg.toolCalls = [
                  ...(lastMsg.toolCalls || []),
                  { id: toolId, name: toolName, status: 'running' },
                ];
              }
              return [...newMessages];
            });
          },

          onToolEnd: (toolId, toolName, resultPreview) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMsg = newMessages[assistantIndex];
              if (lastMsg?.role === 'assistant' && lastMsg.toolCalls) {
                lastMsg.toolCalls = lastMsg.toolCalls.map((tc) =>
                  tc.id === toolId
                    ? { ...tc, status: 'completed' as const, resultPreview }
                    : tc
                );
              }
              return [...newMessages];
            });
          },

          onTextDelta: (text) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMsg = newMessages[assistantIndex];
              if (lastMsg?.role === 'assistant') {
                lastMsg.content += text;
              }
              return [...newMessages];
            });
          },

          onMessageComplete: (content) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMsg = newMessages[assistantIndex];
              if (lastMsg?.role === 'assistant') {
                lastMsg.content = content;
                lastMsg.isStreaming = false;
              }
              return [...newMessages];
            });
          },

          onMetadata: (newConversationId, riskAlert) => {
            setConversationId(newConversationId);
            if (riskAlert) {
              setShowCrisisModal(true);
            }
          },

          onError: (errorMessage) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMsg = newMessages[assistantIndex];
              if (lastMsg?.role === 'assistant') {
                lastMsg.error = errorMessage;
                lastMsg.isStreaming = false;
              }
              return [...newMessages];
            });
          },
        }
      );
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMsg = newMessages[assistantIndex];
        if (lastMsg?.role === 'assistant') {
          lastMsg.error = t('errorMessage');
          lastMsg.isStreaming = false;
        }
        return [...newMessages];
      });
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
    <div className="flex flex-col h-full bg-background" role="main" aria-label={t('chatTitle', { defaultValue: 'AI Chat' })}>
      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto"
        role="log"
        aria-label={t('messageHistory', { defaultValue: 'Message history' })}
        aria-live="polite"
        aria-relevant="additions"
      >
        <div className="flex flex-col min-h-full p-4 space-y-6">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground p-8">
              <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-4" aria-hidden="true">
                <span className="text-3xl">👋</span>
              </div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">{t('welcomeTitle')}</h3>
              <p className="max-w-xs text-sm">{t('welcomeMessage')}</p>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => {
                if (msg.role === 'user') {
                  return (
                    <div
                      key={idx}
                      className="flex gap-3 flex-row-reverse animate-message-right"
                      role="article"
                      aria-label={t('yourMessage', { defaultValue: 'Your message' })}
                    >
                      <Avatar className="w-8 h-8" aria-hidden="true">
                        <AvatarFallback className="bg-primary text-primary-foreground">
                          ME
                        </AvatarFallback>
                      </Avatar>
                      <div className="max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm bg-primary text-primary-foreground rounded-tr-sm">
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  );
                }

                // Assistant message with error
                if (msg.error) {
                  return (
                    <ErrorMessage
                      key={idx}
                      message={msg.error}
                    />
                  );
                }

                // Assistant message - streaming or complete
                return (
                  <StreamingMessage
                    key={idx}
                    isStreaming={msg.isStreaming || false}
                    content={msg.content}
                    toolCalls={msg.toolCalls || []}
                  />
                );
              })}
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
          role="form"
          aria-label={t('sendMessageForm', { defaultValue: 'Send message form' })}
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('placeholder')}
            className="rounded-full pl-6 pr-6 py-6 border-0 bg-muted/50 focus-visible:ring-1 focus-visible:bg-background shadow-inner resize-none"
            disabled={loading}
            aria-label={t('messageInput', { defaultValue: 'Type your message' })}
          />
          <Button
            type="submit"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            size="icon"
            className="h-12 w-12 rounded-full shrink-0 shadow-sm"
            aria-label={t('sendButton', { defaultValue: 'Send message' })}
          >
            <Send className="w-5 h-5 ml-0.5" aria-hidden="true" />
          </Button>
        </form>
        {/* Disclaimer */}
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
