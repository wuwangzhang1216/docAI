'use client';

import { useEffect, useState } from 'react';
import { NextIntlClientProvider } from 'next-intl';
import { Inter } from 'next/font/google';
import { useAuth } from '@/lib/auth';
import { useI18n } from '@/lib/i18n';
import { getMessages } from '@/i18n/config';
import { Toaster } from '@/components/ui/toaster';
import { OfflineIndicator } from '@/components/OfflineIndicator';
import { themeScript } from '@/lib/theme';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const initialize = useAuth((state) => state.initialize);
  const { locale } = useI18n();
  const [messages, setMessages] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    getMessages(locale).then(setMessages);
  }, [locale]);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en';
    }
  }, [locale]);

  if (!messages) {
    return (
      <html lang={locale === 'zh' ? 'zh-CN' : 'en'} suppressHydrationWarning>
        <head>
          <title>Heart Guardian AI</title>
          <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
          <meta name="theme-color" content="#3b82f6" />
          <meta name="apple-mobile-web-app-capable" content="yes" />
          <meta name="apple-mobile-web-app-status-bar-style" content="default" />
          <meta name="apple-mobile-web-app-title" content="HeartGuard" />
          <link rel="manifest" href="/manifest.json" />
          <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
          <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        </head>
        <body className={inter.className} suppressHydrationWarning>
          <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </body>
      </html>
    );
  }

  const appName = (messages as { common?: { appName?: string } }).common?.appName || 'Heart Guardian AI';
  const tagline = (messages as { common?: { tagline?: string } }).common?.tagline || '';

  return (
    <html lang={locale === 'zh' ? 'zh-CN' : 'en'} suppressHydrationWarning>
      <head>
        <title>{appName}</title>
        <meta name="description" content={tagline} />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="HeartGuard" />
        <link rel="manifest" href="/manifest.json" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={inter.className} suppressHydrationWarning>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <OfflineIndicator />
          {children}
          <Toaster />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
