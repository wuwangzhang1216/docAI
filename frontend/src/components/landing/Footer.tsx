'use client'

import { useTranslations } from 'next-intl'

export function Footer() {
  const t = useTranslations('landing')

  return (
    <footer id="about" className="bg-muted/30 border-t border-border">
      <div className="mx-auto max-w-7xl overflow-hidden px-6 py-12 sm:py-16 lg:px-8">
        <p className="mt-10 text-center text-xs leading-5 text-muted-foreground">
          {t('footerCopyright')}
        </p>
      </div>
    </footer>
  )
}
