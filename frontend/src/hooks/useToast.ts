import { create } from 'zustand';

export type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info';

export interface ToastData {
  id: string;
  title?: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
}

interface ToastState {
  toasts: ToastData[];
  addToast: (toast: Omit<ToastData, 'id'>) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

const generateId = () => Math.random().toString(36).substring(2, 9);

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],

  addToast: (toast) => {
    const id = generateId();
    const duration = toast.duration ?? 5000;

    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));

    // 自动移除 toast
    if (duration > 0) {
      setTimeout(() => {
        get().removeToast(id);
      }, duration);
    }

    return id;
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },

  clearToasts: () => {
    set({ toasts: [] });
  },
}));

// 便捷方法
export const toast = {
  success: (title: string, description?: string, duration?: number) => {
    return useToastStore.getState().addToast({
      title,
      description,
      variant: 'success',
      duration,
    });
  },

  error: (title: string, description?: string, duration?: number) => {
    return useToastStore.getState().addToast({
      title,
      description,
      variant: 'error',
      duration,
    });
  },

  warning: (title: string, description?: string, duration?: number) => {
    return useToastStore.getState().addToast({
      title,
      description,
      variant: 'warning',
      duration,
    });
  },

  info: (title: string, description?: string, duration?: number) => {
    return useToastStore.getState().addToast({
      title,
      description,
      variant: 'info',
      duration,
    });
  },

  dismiss: (id: string) => {
    useToastStore.getState().removeToast(id);
  },

  dismissAll: () => {
    useToastStore.getState().clearToasts();
  },
};

// Hook for components
export function useToast() {
  const { toasts, addToast, removeToast, clearToasts } = useToastStore();

  return {
    toasts,
    toast: addToast,
    dismiss: removeToast,
    dismissAll: clearToasts,
    // 便捷方法
    success: toast.success,
    error: toast.error,
    warning: toast.warning,
    info: toast.info,
  };
}
