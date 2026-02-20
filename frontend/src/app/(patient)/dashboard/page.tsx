'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { MessageCircle, Calendar, Heart, Sun, Moon, CloudSun, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { toast } from '@/hooks/useToast'
import { cn } from '@/lib/utils'

const springTransition = { type: 'spring' as const, stiffness: 200, damping: 25 }

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: springTransition },
}

export default function DashboardPage() {
  const t = useTranslations('patient.dashboard')
  const common = useTranslations('common')

  const [selectedMood, setSelectedMood] = useState<number | null>(null)
  const [submittingMood, setSubmittingMood] = useState(false)
  const [firstName, setFirstName] = useState<string>('')

  useEffect(() => {
    api
      .getMyProfile()
      .then((profile) => setFirstName(profile.first_name || ''))
      .catch(() => {})
  }, [])

  const hour = new Date().getHours()
  let greeting = t('greetingMorning')
  let Icon = Sun

  if (hour >= 12 && hour < 17) {
    greeting = t('greetingAfternoon')
    Icon = CloudSun
  } else if (hour >= 17) {
    greeting = t('greetingEvening')
    Icon = Moon
  }

  // Dynamic quote based on day of year
  const quotes = t.raw('quotes') as Array<{ text: string; author: string }>
  const todayQuote = quotes[new Date().getDate() % quotes.length]

  // Quick actions config
  const actions = [
    {
      title: t('talkToAI'),
      desc: t('talkToAIDesc'),
      icon: MessageCircle,
      href: '/conversations',
      color: 'text-blue-500',
      bg: 'bg-blue-500/10',
    },
    {
      title: t('healthCenter'),
      desc: t('healthCenterDesc'),
      icon: Heart,
      href: '/health',
      color: 'text-purple-500',
      bg: 'bg-purple-500/10',
    },
    {
      title: t('appointments'),
      desc: t('appointmentsDesc'),
      icon: Calendar,
      href: '/my-appointments',
      color: 'text-green-500',
      bg: 'bg-green-500/10',
    },
  ]

  const emojis = ['😢', '😕', '😐', '🙂', '😄']
  const moodLabels = [
    t('moodVeryLow'),
    t('moodLow'),
    t('moodNeutral'),
    t('moodGood'),
    t('moodExcellent'),
  ]

  const handleMoodSelect = async (moodIndex: number) => {
    const moodScore = (moodIndex + 1) * 2 // Maps 0-4 to 2,4,6,8,10
    setSelectedMood(moodIndex)
    try {
      setSubmittingMood(true)
      await api.submitCheckin({
        mood_score: moodScore,
        sleep_hours: 7,
        sleep_quality: 3,
        medication_taken: true,
      })
      toast.success(t('moodRecorded'))
    } catch {
      toast.error(common('error'))
      setSelectedMood(null)
    } finally {
      setSubmittingMood(false)
    }
  }

  return (
    <div className="px-4 py-6 md:px-8 md:py-8 pb-28 md:pb-12">
      {/* Hero Greeting Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springTransition}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/[0.08] via-transparent to-primary/[0.04] border border-primary/10 p-6 md:p-8"
      >
        {/* Decorative background orbs */}
        <div className="absolute -top-20 -right-20 w-60 h-60 rounded-full bg-primary/[0.06] blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-40 h-40 rounded-full bg-primary/[0.04] blur-2xl pointer-events-none" />

        <div className="relative flex items-start gap-4 md:gap-5">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ ...springTransition, delay: 0.1 }}
            className="p-3 md:p-4 bg-primary/10 rounded-2xl shrink-0"
          >
            <Icon className="w-7 h-7 md:w-8 md:h-8 text-primary" />
          </motion.div>
          <div className="min-w-0">
            <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold tracking-tight text-foreground">
              {greeting}
              {firstName ? `, ${firstName}` : ''}
            </h1>
            <p className="text-muted-foreground text-sm md:text-base mt-1.5">
              {t('feelingQuestion')}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Main Content - Single Column Layout */}
      <div className="mt-6 md:mt-8 space-y-5 md:space-y-6">
        {/* Quick Mood Check - Full Width */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springTransition, delay: 0.08 }}
        >
          <Card className="border-border/50 shadow-apple-sm overflow-hidden">
            <CardHeader className="pb-2 pt-5 px-5 md:px-6">
              <CardTitle className="text-base font-semibold text-foreground">
                {t('quickMoodCheck')}
              </CardTitle>
            </CardHeader>
            <CardContent className="px-5 md:px-6 pb-5">
              <div className="grid grid-cols-5 gap-2 md:gap-3">
                {emojis.map((emoji, i) => (
                  <motion.button
                    key={i}
                    onClick={() => handleMoodSelect(i)}
                    disabled={submittingMood}
                    aria-label={moodLabels[i]}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={cn(
                      'flex flex-col items-center gap-1.5 md:gap-2 py-3 md:py-4 rounded-xl transition-all duration-200',
                      'bg-muted/30 hover:bg-muted/60',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                      selectedMood === i && 'ring-2 ring-primary bg-primary/10 shadow-apple-sm'
                    )}
                  >
                    <span className="text-2xl md:text-3xl lg:text-4xl leading-none">{emoji}</span>
                    <span
                      className={cn(
                        'text-[10px] md:text-xs font-medium transition-colors duration-200',
                        selectedMood === i ? 'text-primary' : 'text-muted-foreground'
                      )}
                    >
                      {moodLabels[i]}
                    </span>
                  </motion.button>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Primary CTA: Talk to AI */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springTransition, delay: 0.14 }}
        >
          <Link href={actions[0].href}>
            <div className="group relative overflow-hidden rounded-2xl gradient-border shadow-apple-md hover:shadow-apple-lg transition-all duration-300 hover:-translate-y-0.5 cursor-pointer">
              <div className="relative bg-card p-5 md:p-6 flex items-center gap-4 md:gap-5">
                {/* Decorative gradient wash */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/[0.04] via-transparent to-purple-500/[0.04] pointer-events-none" />

                <div className="relative p-3 md:p-4 rounded-2xl bg-blue-500/10">
                  <MessageCircle className="w-6 h-6 md:w-7 md:h-7 text-blue-500" />
                </div>
                <div className="relative flex-1 min-w-0">
                  <h3 className="font-semibold text-base md:text-lg text-foreground">
                    {actions[0].title}
                  </h3>
                  <p className="text-xs md:text-sm text-muted-foreground mt-0.5">
                    {actions[0].desc}
                  </p>
                </div>
                <ArrowRight className="relative w-5 h-5 text-muted-foreground opacity-60 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
              </div>
            </div>
          </Link>
        </motion.div>

        {/* Secondary Actions Grid */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={containerVariants}
          className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4"
        >
          {actions.slice(1).map((action) => (
            <motion.div key={action.title} variants={itemVariants}>
              <Link href={action.href}>
                <Card className="h-full transition-all duration-300 border-border/50 shadow-apple-sm cursor-pointer group hover:shadow-apple-md hover:-translate-y-0.5">
                  <CardContent className="p-4 md:p-5">
                    <div className="flex items-start gap-3 md:gap-4">
                      <div className={cn('p-2.5 md:p-3 rounded-xl shrink-0', action.bg)}>
                        <action.icon className={cn('w-5 h-5 md:w-6 md:h-6', action.color)} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm md:text-base text-foreground">
                          {action.title}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-0.5">{action.desc}</p>
                      </div>
                    </div>
                    <div className="flex justify-end mt-3">
                      <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </motion.div>

        {/* Quote of the Day */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ ...springTransition, delay: 0.22 }}
          className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/[0.06] via-primary/[0.03] to-transparent border border-primary/10 p-6 md:p-8"
        >
          {/* Decorative quote mark */}
          <div
            className="absolute top-3 left-4 md:top-4 md:left-6 text-primary/[0.08] text-6xl md:text-8xl font-serif leading-none select-none pointer-events-none"
            aria-hidden="true"
          >
            &ldquo;
          </div>

          <div className="relative">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-3 md:mb-4">
              {t('quoteOfDay')}
            </p>
            <blockquote className="text-base md:text-lg text-foreground/85 leading-relaxed italic pl-2 md:pl-4">
              &ldquo;{todayQuote.text}&rdquo;
            </blockquote>
            <p className="text-sm text-muted-foreground mt-3 md:mt-4 pl-2 md:pl-4">
              &mdash; {todayQuote.author}
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
