'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { ArrowRight, ShieldCheck, Activity, MessageCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { motion } from 'framer-motion'

const springTransition = { type: 'spring' as const, stiffness: 200, damping: 25 }

export function Hero() {
  const t = useTranslations('landing')

  return (
    <div className="relative overflow-hidden bg-background pt-[120px] pb-16 md:pt-[150px] md:pb-32">
      {/* Background glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/[0.07] rounded-full blur-[60px] md:blur-[120px]" />
        <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] bg-blue-400/[0.05] rounded-full blur-[60px] md:blur-[100px]" />
        <div className="absolute top-1/3 right-1/4 w-[300px] h-[300px] bg-purple-400/[0.05] rounded-full blur-[40px] md:blur-[80px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springTransition }}
            className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl"
          >
            {t('heroTitle1')}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-400 block mt-2">
              {t('heroTitle2')}
            </span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springTransition, delay: 0.1 }}
            className="mt-6 text-lg leading-8 text-muted-foreground max-w-2xl mx-auto"
          >
            {t('heroDescription')}
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springTransition, delay: 0.2 }}
            className="mt-10 flex items-center justify-center gap-x-6"
          >
            <Link href="/login">
              <Button
                size="lg"
                className="h-12 px-8 text-lg rounded-full shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-shadow"
              >
                {t('getStarted')} <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="#features">
              <Button variant="ghost" size="lg" className="h-12 px-8 text-lg rounded-full">
                {t('learnMore')}{' '}
                <span aria-hidden="true" className="ml-2">
                  →
                </span>
              </Button>
            </Link>
          </motion.div>
        </div>

        {/* Feature cards */}
        <div id="features" className="mt-16 sm:mt-24 relative">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ ...springTransition, delay: 0.3 }}
            className="mx-auto max-w-5xl rounded-3xl p-4 bg-muted/30 border border-border/50 backdrop-blur-sm"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 p-8 items-center justify-items-center">
              {[
                {
                  icon: MessageCircle,
                  title: t('featureChat'),
                  desc: t('featureChatDesc'),
                  iconBg: 'bg-blue-500/10',
                  iconColor: 'text-blue-600 dark:text-blue-400',
                },
                {
                  icon: ShieldCheck,
                  title: t('featureSecurity'),
                  desc: t('featureSecurityDesc'),
                  iconBg: 'bg-emerald-500/10',
                  iconColor: 'text-emerald-600 dark:text-emerald-400',
                  elevated: true,
                },
                {
                  icon: Activity,
                  title: t('featureMood'),
                  desc: t('featureMoodDesc'),
                  iconBg: 'bg-purple-500/10',
                  iconColor: 'text-purple-600 dark:text-purple-400',
                },
              ].map((card, i) => (
                <motion.div
                  key={card.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ ...springTransition, delay: 0.4 + i * 0.1 }}
                  whileHover={{
                    y: -4,
                    transition: { type: 'spring', stiffness: 400, damping: 25 },
                  }}
                  className={`flex flex-col items-center gap-4 p-8 rounded-2xl bg-card border border-border/50 shadow-apple-sm hover:shadow-apple-lg transition-shadow duration-300 w-full max-w-xs ${card.elevated ? 'md:-translate-y-8' : ''}`}
                >
                  <div className={`p-3 ${card.iconBg} rounded-full`}>
                    <card.icon className={`w-8 h-8 ${card.iconColor}`} />
                  </div>
                  <h3 className="font-semibold">{card.title}</h3>
                  <p className="text-center text-sm text-muted-foreground">{card.desc}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
