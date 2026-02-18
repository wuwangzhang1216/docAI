'use client'

import { useState } from 'react'
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
  hidden: { opacity: 0, x: -10 },
  visible: { opacity: 1, x: 0, transition: springTransition },
}

export default function DashboardPage() {
  const t = useTranslations('patient.dashboard')
  const common = useTranslations('common')

  const [selectedMood, setSelectedMood] = useState<number | null>(null)
  const [submittingMood, setSubmittingMood] = useState(false)

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
    <div className="px-6 py-10 md:px-8 md:py-8 pb-24 md:pb-8 max-w-4xl md:mx-auto">
      {/* Greeting Section */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springTransition}
        className="flex items-center gap-4"
      >
        <div className="p-3 bg-primary/10 rounded-full">
          <Icon className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{greeting}</h1>
          <p className="text-muted-foreground text-sm">{t('feelingQuestion')}</p>
        </div>
      </motion.div>

      {/* Responsive Grid: single column on mobile, two columns on desktop */}
      <div className="mt-8 grid md:grid-cols-[1fr_320px] gap-6 md:gap-8">
        {/* Left Column: Action Cards */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={containerVariants}
          className="space-y-4 order-2 md:order-1"
        >
          {actions.map((action) => (
            <motion.div key={action.title} variants={itemVariants}>
              <Link href={action.href}>
                <Card className="transition-all duration-300 border-border/50 shadow-apple-sm cursor-pointer group hover:shadow-apple-md hover:-translate-y-0.5">
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className={`p-3 rounded-xl ${action.bg}`}>
                      <action.icon className={`w-6 h-6 ${action.color}`} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold">{action.title}</h3>
                      <p className="text-xs text-muted-foreground">{action.desc}</p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </motion.div>

        {/* Right Column: Mood + Quote */}
        <div className="space-y-6 order-1 md:order-2">
          {/* Mood Quick Select */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springTransition, delay: 0.1 }}
          >
            <Card className="border-border/50 shadow-apple-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium">{t('quickMoodCheck')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between gap-2">
                  {emojis.map((emoji, i) => (
                    <button
                      key={i}
                      onClick={() => handleMoodSelect(i)}
                      disabled={submittingMood}
                      aria-label={moodLabels[i]}
                      className={cn(
                        'text-2xl p-3 hover:bg-muted rounded-xl transition-all duration-200 w-full flex items-center justify-center bg-muted/20 hover:scale-105 active:scale-95 disabled:opacity-50',
                        selectedMood === i && 'ring-2 ring-primary bg-primary/10'
                      )}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Quote of the day */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ ...springTransition, delay: 0.2 }}
            className="text-center p-8 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/10"
          >
            <p className="text-xs text-muted-foreground mb-3">{t('quoteOfDay')}</p>
            <p className="italic text-sm text-foreground/80 leading-relaxed">
              &ldquo;{todayQuote.text}&rdquo;
            </p>
            <p className="text-xs text-muted-foreground mt-3">— {todayQuote.author}</p>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
