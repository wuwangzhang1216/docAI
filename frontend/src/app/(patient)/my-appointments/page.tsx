'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { api, AppointmentListItem, AppointmentStatus } from '@/lib/api'
import { cn } from '@/lib/utils'
import { SegmentedControl } from '@/components/ui/segmented-control'
import { Calendar, Clock, User, XCircle, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'

type TranslationFunction = ReturnType<typeof useTranslations<'patient.appointments'>>

// Status badge component
function StatusBadge({ status, t }: { status: AppointmentStatus; t: TranslationFunction }) {
  const statusConfig: Record<
    AppointmentStatus,
    { key: string; className: string; icon: typeof CheckCircle }
  > = {
    PENDING: {
      key: 'pending',
      className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      icon: Clock,
    },
    CONFIRMED: {
      key: 'confirmed',
      className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      icon: CheckCircle,
    },
    COMPLETED: {
      key: 'completed',
      className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      icon: CheckCircle,
    },
    CANCELLED: {
      key: 'cancelled',
      className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
      icon: XCircle,
    },
    NO_SHOW: {
      key: 'noShow',
      className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      icon: AlertCircle,
    },
  }

  const config = statusConfig[status] || statusConfig.PENDING
  const Icon = config.icon

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium',
        config.className
      )}
    >
      <Icon className="w-3 h-3" />
      {t(`status.${config.key}` as 'status.pending')}
    </span>
  )
}

// Type badge
function TypeBadge({ type, t }: { type: string; t: TranslationFunction }) {
  const typeKeys: Record<string, string> = {
    INITIAL: 'initial',
    FOLLOW_UP: 'followUp',
    EMERGENCY: 'emergency',
    CONSULTATION: 'consultation',
  }

  const key = typeKeys[type]
  return (
    <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
      {key ? t(`type.${key}` as 'type.initial') : type}
    </span>
  )
}

// Appointment card for patient
function AppointmentCard({
  appointment,
  onCancel,
  isLoading,
  t,
  weekdays,
}: {
  appointment: AppointmentListItem
  onCancel: () => void
  isLoading: boolean
  t: TranslationFunction
  weekdays: string[]
}) {
  const formatDate = (date: string) => {
    const d = new Date(date)
    return `${d.getMonth() + 1}/${d.getDate()} ${weekdays[d.getDay()]}`
  }

  const formatTime = (time: string) => time.slice(0, 5)

  const isUpcoming = !appointment.is_past && ['PENDING', 'CONFIRMED'].includes(appointment.status)

  return (
    <div
      className={cn(
        'bg-card border rounded-xl p-4 transition-all',
        isUpcoming ? 'border-primary/30 shadow-sm' : 'border-border'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            <User className="w-5 h-5 text-primary" />
          </div>
          <div>
            <div className="font-semibold text-foreground">
              {appointment.doctor?.full_name || t('doctor')}
            </div>
            {appointment.doctor?.specialty && (
              <div className="text-xs text-muted-foreground">{appointment.doctor.specialty}</div>
            )}
          </div>
        </div>
        <StatusBadge status={appointment.status} t={t} />
      </div>

      {/* Details */}
      <div className="space-y-2 mb-3">
        <div className="flex items-center gap-2 text-sm">
          <Calendar className="w-4 h-4 text-muted-foreground" />
          <span className="text-foreground">{formatDate(appointment.appointment_date)}</span>
          <TypeBadge type={appointment.appointment_type} t={t} />
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Clock className="w-4 h-4 text-muted-foreground" />
          <span className="text-foreground">
            {formatTime(appointment.start_time)} - {formatTime(appointment.end_time)}
          </span>
        </div>
      </div>

      {appointment.reason && (
        <p className="text-sm text-muted-foreground border-t border-border pt-2 line-clamp-2">
          {appointment.reason}
        </p>
      )}

      {/* Actions */}
      {appointment.is_cancellable && !appointment.is_past && (
        <div className="mt-3 pt-3 border-t border-border">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="w-full py-2 px-4 text-sm text-destructive bg-destructive/10 rounded-lg hover:bg-destructive/20 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <XCircle className="w-4 h-4" />
                {t('cancelAppointment')}
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}

export default function PatientAppointmentsPage() {
  const t = useTranslations('patient.appointments')
  const weekdays = t.raw('weekdays') as string[]

  const [appointments, setAppointments] = useState<AppointmentListItem[]>([])
  const [upcomingAppointments, setUpcomingAppointments] = useState<AppointmentListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [cancelLoading, setCancelLoading] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'upcoming' | 'all'>('upcoming')
  const [error, setError] = useState<string | null>(null)

  const loadAppointments = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [upcoming, all] = await Promise.all([
        api.getPatientUpcomingAppointments(),
        api.getPatientAppointments(undefined, false, 50),
      ])
      setUpcomingAppointments(upcoming)
      setAppointments(all)
    } catch (err) {
      console.error('Failed to load appointments:', err)
      setError(t('loadError'))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadAppointments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleCancel = async (appointmentId: string) => {
    setCancelLoading(appointmentId)
    try {
      await api.cancelAppointmentByPatient(appointmentId)
      await loadAppointments()
    } catch (err) {
      console.error('Failed to cancel appointment:', err)
      setError(t('cancelError'))
    } finally {
      setCancelLoading(null)
    }
  }

  const displayedAppointments = activeTab === 'upcoming' ? upcomingAppointments : appointments

  if (isLoading) {
    return (
      <div className="p-4 space-y-4 pb-28">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-muted animate-shimmer" />
          <div className="space-y-2">
            <div className="h-5 w-36 rounded bg-muted animate-shimmer" />
            <div className="h-3 w-28 rounded bg-muted animate-shimmer" />
          </div>
        </div>
        <div className="h-10 rounded-xl bg-muted animate-shimmer" />
        <div className="space-y-3">
          <div className="h-36 rounded-xl bg-muted animate-shimmer" />
          <div className="h-36 rounded-xl bg-muted animate-shimmer" />
          <div className="h-36 rounded-xl bg-muted animate-shimmer" />
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 pb-28 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
          <Calendar className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-foreground">{t('title')}</h1>
          <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
        </div>
      </div>

      {/* Tabs */}
      <SegmentedControl
        value={activeTab}
        onChange={setActiveTab}
        options={[
          {
            value: 'upcoming' as const,
            label: `${t('tabs.upcoming')} (${upcomingAppointments.length})`,
          },
          { value: 'all' as const, label: t('tabs.all') },
        ]}
      />

      {/* Error */}
      {error && (
        <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Appointments List */}
      {displayedAppointments.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
            <Calendar className="w-8 h-8 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground mb-2">
            {activeTab === 'upcoming' ? t('empty.upcoming') : t('empty.all')}
          </p>
          <p className="text-sm text-muted-foreground">{t('emptyHint')}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayedAppointments.map((apt) => (
            <AppointmentCard
              key={apt.id}
              appointment={apt}
              onCancel={() => handleCancel(apt.id)}
              isLoading={cancelLoading === apt.id}
              t={t}
              weekdays={weekdays}
            />
          ))}
        </div>
      )}

      {/* Upcoming notice */}
      {activeTab === 'upcoming' && upcomingAppointments.length > 0 && (
        <div className="mt-4 p-4 bg-primary/5 border border-primary/20 rounded-xl">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-4 h-4 text-primary" />
            </div>
            <div className="text-sm">
              <p className="font-medium text-foreground mb-1">{t('reminder.title')}</p>
              <ul className="text-muted-foreground space-y-1">
                <li>- {t('reminder.tip1')}</li>
                <li>- {t('reminder.tip2')}</li>
                <li>- {t('reminder.tip3')}</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
