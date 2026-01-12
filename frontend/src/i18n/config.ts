import type { Locale } from '@/lib/i18n';

export const locales = ['en', 'zh', 'fr', 'es', 'fa', 'hi', 'pa', 'bn', 'ur', 'ta', 'ht', 'ar'] as const;

// Language names for display in language selector
export const localeNames: Record<string, string> = {
  en: 'English',
  zh: '中文',
  fr: 'Français',
  es: 'Español',
  fa: 'فارسی',
  hi: 'हिन्दी',
  pa: 'ਪੰਜਾਬੀ',
  bn: 'বাংলা',
  ur: 'اردو',
  ta: 'தமிழ்',
  ht: 'Kreyòl Ayisyen',
  ar: 'العربية'
};
export const defaultLocale: Locale = 'en';

export async function getMessages(locale: Locale) {
  try {
    return (await import(`./locales/${locale}.json`)).default;
  } catch {
    return (await import(`./locales/${defaultLocale}.json`)).default;
  }
}
