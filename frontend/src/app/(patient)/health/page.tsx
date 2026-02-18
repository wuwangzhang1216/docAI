'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { api } from '@/lib/api'
import {
  Heart,
  ClipboardList,
  FileText,
  Moon,
  Pill,
  TrendingUp,
  ChevronRight,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CheckinRecord {
  id: string
  checkin_date: string
  mood_score: number
  sleep_hours: number
  sleep_quality: number
  medication_taken: boolean
  notes?: string
  created_at: string
}

interface Assessment {
  id: string
  assessment_type: string
  total_score: number
  severity: string
  created_at: string
}

export default function HealthPage() {
  const t = useTranslations('patient.health')
  const checkinT = useTranslations('patient.checkin')
  const common = useTranslations('common')

  const [todayCheckin, setTodayCheckin] = useState<CheckinRecord | null>(null)
  const [recentCheckins, setRecentCheckins] = useState<CheckinRecord[]>([])
  const [recentAssessments, setRecentAssessments] = useState<Assessment[]>([])
  const [loading, setLoading] = useState(true)

  const moodEmojis = ['😢', '😔', '😐', '🙂', '😊']

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch today's checkin
        const existing = await api.getTodayCheckin()
        if (existing) {
          setTodayCheckin(existing)
        }

        // Fetch recent check-ins (last 7 days)
        const endDate = new Date().toISOString().split('T')[0]
        const startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        const history = await api.getCheckins(startDate, endDate)
        setRecentCheckins(history)

        // Fetch recent assessments
        try {
          const assessments = await api.getAssessments()
          setRecentAssessments(assessments.slice(0, 3))
        } catch {
          // Assessments might not exist yet
          setRecentAssessments([])
        }
      } catch (error) {
        console.error('Error fetching health data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const getMoodEmoji = (score: number) => {
    const index = Math.min(Math.floor(score / 2.5), 4)
    return moodEmojis[index]
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
  }

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      MINIMAL: 'text-green-600 dark:text-green-400 bg-green-500/10',
      MILD: 'text-yellow-600 dark:text-yellow-400 bg-yellow-500/10',
      MODERATE: 'text-orange-600 dark:text-orange-400 bg-orange-500/10',
      MODERATELY_SEVERE: 'text-red-500 dark:text-red-400 bg-red-500/10',
      SEVERE: 'text-red-700 dark:text-red-400 bg-red-500/20',
    }
    return colors[severity] || 'text-gray-600 bg-gray-100'
  }

  const getSeverityLabel = (severity: string) => {
    const labels: Record<string, string> = {
      MINIMAL: t('severity.minimal', { defaultValue: 'Minimal' }),
      MILD: t('severity.mild', { defaultValue: 'Mild' }),
      MODERATE: t('severity.moderate', { defaultValue: 'Moderate' }),
      MODERATELY_SEVERE: t('severity.moderatelySevere', { defaultValue: 'Moderately Severe' }),
      SEVERE: t('severity.severe', { defaultValue: 'Severe' }),
    }
    return labels[severity] || severity
  }

  // Get sleep quality labels from translations
  const sleepLabels = checkinT.raw('sleepLabels') as string[]

  if (loading) {
    return (
      <div className="h-full overflow-y-auto p-4 space-y-4 pb-28 md:pb-8 max-w-3xl md:mx-auto">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-muted animate-shimmer" />
          <div className="space-y-2">
            <div className="h-5 w-32 rounded bg-muted animate-shimmer" />
            <div className="h-3 w-24 rounded bg-muted animate-shimmer" />
          </div>
        </div>
        <div className="h-24 rounded-xl bg-muted animate-shimmer" />
        <div className="grid grid-cols-2 gap-4">
          <div className="h-32 rounded-xl bg-muted animate-shimmer" />
          <div className="h-32 rounded-xl bg-muted animate-shimmer" />
        </div>
        <div className="h-40 rounded-xl bg-muted animate-shimmer" />
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4 pb-28 md:pb-8 max-w-3xl md:mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="bg-primary/10 p-2 rounded-xl">
          <Heart className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-bold">{t('title', { defaultValue: 'Health Center' })}</h1>
          <p className="text-sm text-muted-foreground">
            {t('subtitle', { defaultValue: 'Track your well-being' })}
          </p>
        </div>
      </div>

      {/* Today's Status Card */}
      <Card className="border-border/50 shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            {t('todayStatus', { defaultValue: "Today's Status" })}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {todayCheckin ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <span className="text-2xl">{getMoodEmoji(todayCheckin.mood_score)}</span>
                  <p className="text-xs text-muted-foreground mt-1">
                    {t('mood', { defaultValue: 'Mood' })}
                  </p>
                </div>
                <div className="text-center">
                  <div className="flex items-center gap-1">
                    <Moon className="w-4 h-4 text-indigo-500" />
                    <span className="font-medium">{todayCheckin.sleep_hours}h</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {t('sleep', { defaultValue: 'Sleep' })}
                  </p>
                </div>
                <div className="text-center">
                  <div
                    className={`flex items-center gap-1 ${todayCheckin.medication_taken ? 'text-green-600' : 'text-red-500'}`}
                  >
                    <Pill className="w-4 h-4" />
                    <span className="font-medium">{todayCheckin.medication_taken ? '✓' : '✗'}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {t('meds', { defaultValue: 'Meds' })}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-xs font-medium">
                  {t('checkedIn', { defaultValue: 'Checked in' })}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-muted-foreground">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">
                  {t('notCheckedIn', { defaultValue: "You haven't checked in today" })}
                </span>
              </div>
              <Link href="/checkin" className="text-sm font-medium text-primary hover:underline">
                {t('checkInNow', { defaultValue: 'Check in now' })} →
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Action Cards */}
      <div className="grid grid-cols-2 gap-4">
        {/* Daily Check-in Card */}
        <Link href="/checkin">
          <Card className="h-full border-border/50 shadow-sm hover:shadow-md transition-shadow cursor-pointer group">
            <CardContent className="p-4 flex flex-col items-center text-center">
              <div className="bg-purple-500/10 p-3 rounded-xl mb-3 group-hover:scale-105 transition-transform">
                <ClipboardList className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="font-semibold text-foreground">
                {t('dailyCheckin', { defaultValue: 'Daily Check-in' })}
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                {t('dailyCheckinDesc', { defaultValue: 'Log mood, sleep & meds' })}
              </p>
            </CardContent>
          </Card>
        </Link>

        {/* Mental Health Assessment Card */}
        <Link href="/assessment">
          <Card className="h-full border-border/50 shadow-sm hover:shadow-md transition-shadow cursor-pointer group">
            <CardContent className="p-4 flex flex-col items-center text-center">
              <div className="bg-blue-500/10 p-3 rounded-xl mb-3 group-hover:scale-105 transition-transform">
                <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="font-semibold text-foreground">
                {t('assessment', { defaultValue: 'Assessment' })}
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                {t('assessmentDesc', { defaultValue: 'PHQ-9, GAD-7, PCL-5' })}
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Recent Check-ins */}
      {recentCheckins.length > 0 && (
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium">
                {t('recentCheckins', { defaultValue: 'Recent Check-ins' })}
              </CardTitle>
              <Link
                href="/checkin"
                className="text-xs text-primary hover:underline flex items-center gap-1"
              >
                {t('viewAll', { defaultValue: 'View all' })}
                <ChevronRight className="w-3 h-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="divide-y divide-border">
              {recentCheckins.slice(0, 5).map((checkin) => (
                <div key={checkin.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {formatDate(checkin.checkin_date)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {checkin.sleep_hours}h {t('sleep', { defaultValue: 'sleep' })} ·{' '}
                      {sleepLabels[checkin.sleep_quality - 1]}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{getMoodEmoji(checkin.mood_score)}</span>
                    <span className="text-sm text-muted-foreground">{checkin.mood_score}/10</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Assessments */}
      {recentAssessments.length > 0 && (
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium">
                {t('recentAssessments', { defaultValue: 'Recent Assessments' })}
              </CardTitle>
              <Link
                href="/assessment"
                className="text-xs text-primary hover:underline flex items-center gap-1"
              >
                {t('takeNew', { defaultValue: 'Take new' })}
                <ChevronRight className="w-3 h-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="divide-y divide-border">
              {recentAssessments.map((assessment) => (
                <div key={assessment.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {assessment.assessment_type}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(assessment.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{assessment.total_score}</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${getSeverityColor(assessment.severity)}`}
                    >
                      {getSeverityLabel(assessment.severity)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty state for new users */}
      {recentCheckins.length === 0 && recentAssessments.length === 0 && (
        <Card className="border-border/50 shadow-sm">
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Heart className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="font-semibold text-foreground mb-2">
              {t('getStarted', { defaultValue: 'Get Started' })}
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              {t('getStartedDesc', {
                defaultValue:
                  'Start tracking your mental health by completing a daily check-in or taking an assessment.',
              })}
            </p>
            <div className="flex gap-3 justify-center">
              <Link
                href="/checkin"
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                {t('firstCheckin', { defaultValue: 'First Check-in' })}
              </Link>
              <Link
                href="/assessment"
                className="px-4 py-2 border border-border text-foreground rounded-lg text-sm font-medium hover:bg-muted transition-colors"
              >
                {t('firstAssessment', { defaultValue: 'Take Assessment' })}
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
