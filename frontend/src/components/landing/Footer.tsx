'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { HeartGuardianLogo } from '@/components/ui/HeartGuardianLogo'

export function Footer() {
  const t = useTranslations('landing')

  return (
    <footer id="about" className="bg-muted/30 border-t border-border">
      <div className="mx-auto max-w-7xl px-6 py-12 sm:py-16 lg:px-8">
        {/* Logo + Disclaimer */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-muted/60 dark:bg-white/[0.06] p-1.5 rounded-lg">
              <HeartGuardianLogo className="w-5 h-5" />
            </div>
            <span className="text-sm font-semibold text-foreground">{t('brandName')}</span>
          </div>
          <p className="text-xs text-muted-foreground max-w-md leading-relaxed">
            {t('footerDisclaimer')}
          </p>
        </div>

        {/* Links */}
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 mb-8">
          <Link
            href="/privacy"
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {t('footerPrivacy')}
          </Link>
          <Link
            href="/terms"
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {t('footerTerms')}
          </Link>
          <Link
            href="/crisis"
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {t('footerCrisisResources')}
          </Link>
          <Link
            href="/contact"
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {t('footerContact')}
          </Link>
        </div>

        {/* Copyright */}
        <p className="text-center text-xs leading-5 text-muted-foreground">
          {t('footerCopyright')}
        </p>
      </div>
    </footer>
  )
}
