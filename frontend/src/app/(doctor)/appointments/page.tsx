'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { api, AppointmentListItem, CalendarMonthView, AppointmentStats, AppointmentStatus } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  CalendarIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlusIcon,
  ClockIcon,
  CheckIcon,
  XMarkIcon,
  AlertCircleIcon,
  Loader2Icon,
} from '@/components/ui/icons';

// Status badge component
function StatusBadge({ status, t }: { status: AppointmentStatus; t: ReturnType<typeof useTranslations<'doctor.appointments'>> }) {
  const statusConfig: Record<AppointmentStatus, { key: string; className: string }> = {
    PENDING: { key: 'pending', className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' },
    CONFIRMED: { key: 'confirmed', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' },
    COMPLETED: { key: 'completed', className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' },
    CANCELLED: { key: 'cancelled', className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
    NO_SHOW: { key: 'noShow', className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' },
  };

  const config = statusConfig[status] || statusConfig.PENDING;
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', config.className)}>
      {t(`status.${config.key}` as 'status.pending')}
    </span>
  );
}

// Type badge component
function TypeBadge({ type, t }: { type: string; t: ReturnType<typeof useTranslations<'doctor.appointments'>> }) {
  const typeConfig: Record<string, { key: string; className: string }> = {
    INITIAL: { key: 'initial', className: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400' },
    FOLLOW_UP: { key: 'followUp', className: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400' },
    EMERGENCY: { key: 'emergency', className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' },
    CONSULTATION: { key: 'consultation', className: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400' },
  };

  const config = typeConfig[type] || typeConfig.FOLLOW_UP;
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', config.className)}>
      {t(`type.${config.key}` as 'type.initial')}
    </span>
  );
}

// Calendar component
function AppointmentCalendar({
  year,
  month,
  calendarData,
  onDateSelect,
  selectedDate,
  t,
}: {
  year: number;
  month: number;
  calendarData: CalendarMonthView | null;
  onDateSelect: (date: string) => void;
  selectedDate: string | null;
  t: ReturnType<typeof useTranslations<'doctor.appointments'>>;
}) {
  const daysOfWeek = t.raw('calendar.daysOfWeek') as string[];

  const firstDay = new Date(year, month - 1, 1);
  const lastDay = new Date(year, month, 0);
  const startPadding = firstDay.getDay();
  const totalDays = lastDay.getDate();

  const appointmentsByDate: Record<string, number> = {};
  calendarData?.days.forEach((day) => {
    appointmentsByDate[day.date] = day.total_count;
  });

  const days: (number | null)[] = [];
  for (let i = 0; i < startPadding; i++) {
    days.push(null);
  }
  for (let i = 1; i <= totalDays; i++) {
    days.push(i);
  }

  const today = new Date();
  const todayStr = today.toISOString().split('T')[0];

  return (
    <div className="bg-card rounded-xl border border-border p-4">
      <div className="grid grid-cols-7 gap-1 text-center mb-2">
        {daysOfWeek.map((day) => (
          <div key={day} className="text-xs font-medium text-muted-foreground py-2">
            {day}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {days.map((day, idx) => {
          if (day === null) {
            return <div key={`empty-${idx}`} className="aspect-square" />;
          }

          const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          const count = appointmentsByDate[dateStr] || 0;
          const isToday = dateStr === todayStr;
          const isSelected = dateStr === selectedDate;

          return (
            <button
              key={day}
              onClick={() => onDateSelect(dateStr)}
              className={cn(
                'aspect-square flex flex-col items-center justify-center rounded-lg text-sm transition-all',
                isToday && 'ring-2 ring-primary ring-offset-2 ring-offset-background',
                isSelected && 'bg-primary text-primary-foreground',
                !isSelected && 'hover:bg-muted',
                count > 0 && !isSelected && 'font-semibold'
              )}
            >
              <span>{day}</span>
              {count > 0 && (
                <span className={cn(
                  'text-[10px] leading-none mt-0.5',
                  isSelected ? 'text-primary-foreground/80' : 'text-primary'
                )}>
                  {count}{t('calendar.appointments')}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Appointment card component
function AppointmentCard({
  appointment,
  onConfirm,
  onComplete,
  onCancel,
  onNoShow,
  isLoading,
  t,
}: {
  appointment: AppointmentListItem;
  onConfirm: () => void;
  onComplete: () => void;
  onCancel: () => void;
  onNoShow: () => void;
  isLoading: boolean;
  t: ReturnType<typeof useTranslations<'doctor.appointments'>>;
}) {
  const formatTime = (time: string) => time.slice(0, 5);

  return (
    <div className="bg-card border border-border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-foreground">
              {appointment.patient?.full_name || t('unknownPatient')}
            </span>
            <TypeBadge type={appointment.appointment_type} t={t} />
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ClockIcon className="w-4 h-4" />
            <span>
              {formatTime(appointment.start_time)} - {formatTime(appointment.end_time)}
            </span>
          </div>
        </div>
        <StatusBadge status={appointment.status} t={t} />
      </div>

      {appointment.reason && (
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
          {appointment.reason}
        </p>
      )}

      {appointment.is_cancellable && !appointment.is_past && (
        <div className="flex flex-wrap gap-2 pt-2 border-t border-border">
          {appointment.status === 'PENDING' && (
            <button
              onClick={onConfirm}
              disabled={isLoading}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              <CheckIcon className="w-3 h-3" />
              {t('actions.confirm')}
            </button>
          )}
          {(appointment.status === 'PENDING' || appointment.status === 'CONFIRMED') && (
            <>
              <button
                onClick={onComplete}
                disabled={isLoading}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                <CheckIcon className="w-3 h-3" />
                {t('actions.complete')}
              </button>
              <button
                onClick={onNoShow}
                disabled={isLoading}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50 transition-colors"
              >
                <AlertCircleIcon className="w-3 h-3" />
                {t('actions.noShow')}
              </button>
              <button
                onClick={onCancel}
                disabled={isLoading}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 disabled:opacity-50 transition-colors"
              >
                <XMarkIcon className="w-3 h-3" />
                {t('actions.cancel')}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// Stats card component
function StatsCard({ stats, t }: { stats: AppointmentStats | null; t: ReturnType<typeof useTranslations<'doctor.appointments'>> }) {
  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <div className="bg-card border border-border rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-primary">{stats.today_count}</div>
        <div className="text-xs text-muted-foreground">{t('stats.todayCount')}</div>
      </div>
      <div className="bg-card border border-border rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
        <div className="text-xs text-muted-foreground">{t('stats.pending')}</div>
      </div>
      <div className="bg-card border border-border rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-blue-600">{stats.confirmed}</div>
        <div className="text-xs text-muted-foreground">{t('stats.confirmed')}</div>
      </div>
      <div className="bg-card border border-border rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-green-600">{stats.this_week_count}</div>
        <div className="text-xs text-muted-foreground">{t('stats.weekTotal')}</div>
      </div>
    </div>
  );
}

// Create appointment modal
function CreateAppointmentModal({
  isOpen,
  onClose,
  onCreated,
  t,
}: {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
  t: ReturnType<typeof useTranslations<'doctor.appointments'>>;
}) {
  const common = useTranslations('common');
  const [patients, setPatients] = useState<Array<{ id: string; name: string }>>([]);
  const [formData, setFormData] = useState({
    patient_id: '',
    appointment_date: '',
    start_time: '',
    end_time: '',
    appointment_type: 'FOLLOW_UP',
    reason: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadPatients();
    }
  }, [isOpen]);

  const loadPatients = async () => {
    try {
      const result = await api.getDoctorPatients({ limit: 100 });
      setPatients(result.items.map((p) => ({ id: p.patient_id, name: p.patient_name })));
    } catch (err) {
      console.error('Failed to load patients:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await api.createAppointment({
        patient_id: formData.patient_id,
        appointment_date: formData.appointment_date,
        start_time: formData.start_time,
        end_time: formData.end_time,
        appointment_type: formData.appointment_type as 'INITIAL' | 'FOLLOW_UP' | 'EMERGENCY' | 'CONSULTATION',
        reason: formData.reason || undefined,
      });
      onCreated();
      onClose();
      setFormData({
        patient_id: '',
        appointment_date: '',
        start_time: '',
        end_time: '',
        appointment_type: 'FOLLOW_UP',
        reason: '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : t('createFailed'));
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-xl border border-border w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-card border-b border-border p-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{t('createAppointment')}</h2>
          <button onClick={onClose} className="p-1 hover:bg-muted rounded-lg transition-colors">
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">{t('form.patient')} *</label>
            <select
              value={formData.patient_id}
              onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
              required
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="">{t('form.selectPatient')}</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('form.date')} *</label>
            <input
              type="date"
              value={formData.appointment_date}
              onChange={(e) => setFormData({ ...formData, appointment_date: e.target.value })}
              required
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('form.startTime')} *</label>
              <input
                type="time"
                value={formData.start_time}
                onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                required
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('form.endTime')} *</label>
              <input
                type="time"
                value={formData.end_time}
                onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                required
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('form.type')}</label>
            <select
              value={formData.appointment_type}
              onChange={(e) => setFormData({ ...formData, appointment_type: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="INITIAL">{t('type.initial')}</option>
              <option value="FOLLOW_UP">{t('type.followUp')}</option>
              <option value="EMERGENCY">{t('type.emergency')}</option>
              <option value="CONSULTATION">{t('type.consultation')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('form.reason')}</label>
            <textarea
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
              placeholder={t('form.reasonPlaceholder')}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2Icon className="w-4 h-4 animate-spin" />
                {t('creating')}
              </>
            ) : (
              t('createAppointment')
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AppointmentsPage() {
  const t = useTranslations('doctor.appointments');
  const [currentDate, setCurrentDate] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() + 1 };
  });
  const [calendarData, setCalendarData] = useState<CalendarMonthView | null>(null);
  const [appointments, setAppointments] = useState<AppointmentListItem[]>([]);
  const [stats, setStats] = useState<AppointmentStats | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [calendarResult, statsResult] = await Promise.all([
        api.getDoctorCalendar(currentDate.year, currentDate.month),
        api.getDoctorAppointmentStats(),
      ]);
      setCalendarData(calendarResult);
      setStats(statsResult);

      // Load appointments for today by default
      const today = new Date().toISOString().split('T')[0];
      setSelectedDate(today);
      await loadAppointmentsForDate(today);
    } catch (err) {
      console.error('Failed to load appointments data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [currentDate]);

  const loadAppointmentsForDate = async (date: string) => {
    try {
      const result = await api.getDoctorAppointments({
        start_date: date,
        end_date: date,
        limit: 50,
      });
      setAppointments(result);
    } catch (err) {
      console.error('Failed to load appointments for date:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDateSelect = async (date: string) => {
    setSelectedDate(date);
    await loadAppointmentsForDate(date);
  };

  const handlePrevMonth = () => {
    setCurrentDate((prev) => {
      if (prev.month === 1) {
        return { year: prev.year - 1, month: 12 };
      }
      return { year: prev.year, month: prev.month - 1 };
    });
  };

  const handleNextMonth = () => {
    setCurrentDate((prev) => {
      if (prev.month === 12) {
        return { year: prev.year + 1, month: 1 };
      }
      return { year: prev.year, month: prev.month + 1 };
    });
  };

  const handleAction = async (
    appointmentId: string,
    action: 'confirm' | 'complete' | 'cancel' | 'noshow'
  ) => {
    setActionLoading(appointmentId);
    try {
      switch (action) {
        case 'confirm':
          await api.confirmAppointment(appointmentId);
          break;
        case 'complete':
          await api.completeAppointment(appointmentId);
          break;
        case 'cancel':
          await api.cancelAppointmentByDoctor(appointmentId);
          break;
        case 'noshow':
          await api.markAppointmentNoShow(appointmentId);
          break;
      }
      // Reload data
      await loadData();
      if (selectedDate) {
        await loadAppointmentsForDate(selectedDate);
      }
    } catch (err) {
      console.error(`Failed to ${action} appointment:`, err);
    } finally {
      setActionLoading(null);
    }
  };

  const monthNames = t.raw('months') as string[];

  const formatSelectedDate = (date: string) => {
    const d = new Date(date);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center">
          <Loader2Icon className="w-8 h-8 animate-spin text-primary mb-2" />
          <p className="text-muted-foreground text-sm">{t('loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <CalendarIcon className="w-6 h-6" />
            {t('title')}
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            {t('subtitle')}
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          {t('createAppointment')}
        </button>
      </div>

      {/* Stats */}
      <StatsCard stats={stats} t={t} />

      <div className="grid md:grid-cols-3 gap-6">
        {/* Calendar */}
        <div className="md:col-span-1">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={handlePrevMonth}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ChevronLeftIcon className="w-5 h-5" />
            </button>
            <h2 className="font-semibold">
              {currentDate.year} {monthNames[currentDate.month - 1]}
            </h2>
            <button
              onClick={handleNextMonth}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ChevronRightIcon className="w-5 h-5" />
            </button>
          </div>
          <AppointmentCalendar
            year={currentDate.year}
            month={currentDate.month}
            calendarData={calendarData}
            onDateSelect={handleDateSelect}
            selectedDate={selectedDate}
            t={t}
          />
        </div>

        {/* Appointments List */}
        <div className="md:col-span-2">
          <h2 className="text-lg font-semibold mb-4">
            {selectedDate ? formatSelectedDate(selectedDate) : t('selectDateToView')}
          </h2>

          {appointments.length === 0 ? (
            <div className="bg-card border border-border rounded-xl p-8 text-center">
              <CalendarIcon className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
              <p className="text-muted-foreground">{t('noAppointments')}</p>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="mt-4 text-primary hover:underline text-sm"
              >
                {t('createNew')}
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {appointments.map((apt) => (
                <AppointmentCard
                  key={apt.id}
                  appointment={apt}
                  onConfirm={() => handleAction(apt.id, 'confirm')}
                  onComplete={() => handleAction(apt.id, 'complete')}
                  onCancel={() => handleAction(apt.id, 'cancel')}
                  onNoShow={() => handleAction(apt.id, 'noshow')}
                  isLoading={actionLoading === apt.id}
                  t={t}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      <CreateAppointmentModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={loadData}
        t={t}
      />
    </div>
  );
}
