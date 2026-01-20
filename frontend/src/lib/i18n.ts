import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Locale = 'en' | 'zh' | 'fr' | 'es' | 'fa' | 'hi' | 'pa' | 'bn' | 'ur' | 'ta' | 'ht' | 'ar';

interface I18nState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export const useI18n = create<I18nState>()(
  persist(
    (set) => ({
      locale: 'en',
      setLocale: (locale) => {
        set({ locale });
        if (typeof document !== 'undefined') {
          const langMap: Record<Locale, string> = {
            en: 'en',
            zh: 'zh-CN',
            fr: 'fr',
            es: 'es',
            fa: 'fa',
            hi: 'hi',
            pa: 'pa',
            bn: 'bn',
            ur: 'ur',
            ta: 'ta',
            ht: 'ht',
            ar: 'ar'
          };
          document.documentElement.lang = langMap[locale] || 'en';
          // Set RTL direction for Arabic, Persian, and Urdu
          document.documentElement.dir = ['ar', 'fa', 'ur'].includes(locale) ? 'rtl' : 'ltr';
        }
      },
    }),
    {
      name: 'language-preference',
      partialize: (state) => ({ locale: state.locale }),
    }
  )
);
