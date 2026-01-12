'use client';

import { useToastStore } from '@/hooks/useToast';
import { Toast } from './toast';
import { cn } from '@/lib/utils';

export function Toaster() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div
      className={cn(
        'fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:bottom-4 sm:right-4 sm:top-auto sm:flex-col sm:max-w-[420px]'
      )}
      aria-label="通知"
    >
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          variant={toast.variant}
          title={toast.title}
          description={toast.description}
          onClose={() => removeToast(toast.id)}
          className="animate-in slide-in-from-bottom-5 fade-in-0 duration-300"
        />
      ))}
    </div>
  );
}
