'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { CheckCircle2, Moon, Pill, FileText, TrendingUp, Loader2 } from 'lucide-react';
import { Disclosure, DisclosureButton, DisclosurePanel } from '@/components/ui/disclosure';
import { CheckinFormSkeleton } from '@/components/ui/skeleton';
import { toast } from '@/hooks/useToast';

interface CheckinRecord {
  id: string;
  checkin_date: string;
  mood_score: number;
  sleep_hours: number;
  sleep_quality: number;
  medication_taken: boolean;
  notes?: string;
  created_at: string;
}

export default function CheckinPage() {
  const [mood, setMood] = useState(5);
  const [sleepHours, setSleepHours] = useState(7);
  const [sleepQuality, setSleepQuality] = useState(3);
  const [medication, setMedication] = useState(true);
  const [notes, setNotes] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [todayCheckin, setTodayCheckin] = useState<CheckinRecord | null>(null);
  const [recentCheckins, setRecentCheckins] = useState<CheckinRecord[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const t = useTranslations('patient.checkin');
  const common = useTranslations('common');

  const moodEmojis = ['😢', '😔', '😐', '🙂', '😊'];

  useEffect(() => {
    const fetchCheckinData = async () => {
      try {
        // Check if already checked in today
        const existing = await api.getTodayCheckin();
        if (existing) {
          setTodayCheckin(existing);
          setMood(existing.mood_score);
          setSleepHours(existing.sleep_hours);
          setSleepQuality(existing.sleep_quality);
          setMedication(existing.medication_taken);
          setNotes(existing.notes || '');
        }

        // Fetch recent check-ins (last 7 days)
        const endDate = new Date().toISOString().split('T')[0];
        const startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        const history = await api.getCheckins(startDate, endDate);
        setRecentCheckins(history);
      } catch (error) {
        console.error('Error fetching checkin data:', error);
        toast.error(common('error'), t('fetchError', { defaultValue: 'Failed to load check-in data' }));
      } finally {
        setInitialLoading(false);
      }
    };
    fetchCheckinData();
  }, [submitted, common, t]);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const result = await api.submitCheckin({
        mood_score: mood,
        sleep_hours: sleepHours,
        sleep_quality: sleepQuality,
        medication_taken: medication,
        notes: notes || undefined,
      });
      setTodayCheckin(result);
      setSubmitted(true);
      setIsEditing(false);
      toast.success(
        t('successTitle'),
        t('successMessage')
      );
    } catch (error) {
      console.error('Checkin error:', error);
      toast.error(
        common('error'),
        t('submitError', { defaultValue: 'Failed to submit check-in. Please try again.' })
      );
    } finally {
      setLoading(false);
    }
  };

  const getMoodEmoji = (score: number) => {
    const index = Math.min(Math.floor(score / 2.5), 4);
    return moodEmojis[index];
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  };

  // Get sleep quality labels from translations
  const sleepLabels = t.raw('sleepLabels') as string[];

  // Get mood description based on score
  const getMoodDescription = (score: number) => {
    if (score <= 2) return t('moodDescriptions.veryLow', { defaultValue: 'Very Low' });
    if (score <= 4) return t('moodDescriptions.low', { defaultValue: 'Low' });
    if (score <= 6) return t('moodDescriptions.neutral', { defaultValue: 'Neutral' });
    if (score <= 8) return t('moodDescriptions.good', { defaultValue: 'Good' });
    return t('moodDescriptions.excellent', { defaultValue: 'Excellent' });
  };

  // Show loading skeleton during initial load
  if (initialLoading) {
    return (
      <div className="h-full overflow-y-auto p-4 max-w-2xl md:mx-auto">
        <CheckinFormSkeleton />
      </div>
    );
  }

  // Show today's check-in record (either just submitted or already exists)
  if ((todayCheckin && !isEditing) || submitted) {
    const record = todayCheckin;
    return (
      <div className="h-full overflow-y-auto p-4 space-y-4 max-w-2xl md:mx-auto">
        {/* Success Header */}
        <div className="bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle2 className="w-8 h-8" />
            <div>
              <h2 className="text-xl font-bold">{t('successTitle')}</h2>
              <p className="text-green-100 text-sm">{t('successMessage')}</p>
            </div>
          </div>
        </div>

        {/* Today's Record */}
        {record && (
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-semibold text-foreground flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-500" />
              {t('todayRecord', { defaultValue: "Today's Check-in" })}
            </h3>

            {/* Mood */}
            <div className="flex items-center justify-between py-3 border-b border-border">
              <span className="text-muted-foreground">{t('moodQuestion')}</span>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getMoodEmoji(record.mood_score)}</span>
                <span className="font-semibold text-lg text-foreground">{record.mood_score}/10</span>
              </div>
            </div>

            {/* Sleep */}
            <div className="flex items-center justify-between py-3 border-b border-border">
              <span className="text-muted-foreground flex items-center gap-2">
                <Moon className="w-4 h-4" />
                {t('sleepDuration')}
              </span>
              <span className="font-semibold text-foreground">{record.sleep_hours} {t('hours')}</span>
            </div>

            {/* Sleep Quality */}
            <div className="flex items-center justify-between py-3 border-b border-border">
              <span className="text-muted-foreground">{t('sleepQuality')}</span>
              <span className="font-semibold text-foreground">{sleepLabels[record.sleep_quality - 1]}</span>
            </div>

            {/* Medication */}
            <div className="flex items-center justify-between py-3 border-b border-border">
              <span className="text-muted-foreground flex items-center gap-2">
                <Pill className="w-4 h-4" />
                {t('medicationQuestion')}
              </span>
              <span className={`font-semibold ${record.medication_taken ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>
                {record.medication_taken ? '✓ ' + t('medicationYes') : '✗ ' + t('medicationNo')}
              </span>
            </div>

            {/* Notes */}
            {record.notes && (
              <div className="py-3">
                <span className="text-muted-foreground flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4" />
                  {t('notesLabel')}
                </span>
                <p className="text-foreground bg-muted rounded-lg p-3">{record.notes}</p>
              </div>
            )}
          </div>
        )}

        {/* Edit Button */}
        <button
          onClick={() => {
            setIsEditing(true);
            setSubmitted(false);
          }}
          className="w-full bg-muted text-foreground py-3 rounded-xl font-medium hover:bg-muted/80 transition-colors"
        >
          {t('updateButton')}
        </button>

        {/* Recent History */}
        {recentCheckins.length > 1 && (
          <Disclosure>
            <DisclosureButton className="text-foreground">
              <span className="font-semibold">{t('recentHistory', { defaultValue: 'Recent Check-ins' })}</span>
            </DisclosureButton>

            <DisclosurePanel className="p-0">
              <div className="border-t border-border divide-y divide-border">
                {recentCheckins
                  .filter(c => c.id !== todayCheckin?.id)
                  .slice(0, 6)
                  .map((checkin) => (
                    <div key={checkin.id} className="p-4 flex items-center justify-between">
                      <div>
                        <p className="font-medium text-foreground">{formatDate(checkin.checkin_date)}</p>
                        <p className="text-sm text-muted-foreground">
                          {t('sleepDuration')}: {checkin.sleep_hours}h
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="text-2xl">{getMoodEmoji(checkin.mood_score)}</span>
                        <p className="text-sm text-muted-foreground">{checkin.mood_score}/10</p>
                      </div>
                    </div>
                  ))}
              </div>
            </DisclosurePanel>
          </Disclosure>
        )}
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4 max-w-2xl md:mx-auto">
      <h1 className="text-xl font-bold">
        {t('title')}
      </h1>

      {/* Mood */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <label className="block text-foreground mb-4">{t('moodQuestion')}</label>
        <div className="flex justify-between items-center mb-4">
          {moodEmojis.map((emoji, idx) => (
            <button
              key={idx}
              onClick={() => setMood(idx * 2.5)}
              className={`text-3xl transition-all duration-200 ${Math.round(mood / 2.5) === idx
                ? 'scale-125 drop-shadow-lg'
                : 'opacity-40 hover:opacity-70 hover:scale-110'
              }`}
              aria-label={`Set mood to ${idx * 2.5}`}
            >
              {emoji}
            </button>
          ))}
        </div>

        {/* Enhanced slider with value indicator */}
        <div className="relative pt-6 pb-2">
          {/* Current value badge */}
          <div
            className="absolute -top-1 transform -translate-x-1/2 transition-all duration-150"
            style={{ left: `${(mood / 10) * 100}%` }}
          >
            <div className="bg-blue-500 text-white text-sm font-bold px-3 py-1 rounded-full shadow-lg">
              {mood}
            </div>
            <div className="w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-blue-500 mx-auto" />
          </div>

          <input
            type="range"
            min="0"
            max="10"
            step="1"
            value={mood}
            onChange={(e) => setMood(Number(e.target.value))}
            className="w-full h-2 bg-gradient-to-r from-red-300 via-yellow-300 to-green-300 rounded-lg appearance-none cursor-pointer
                       [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                       [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-blue-500
                       [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:cursor-pointer
                       [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-110"
            aria-label={t('moodQuestion')}
            aria-valuemin={0}
            aria-valuemax={10}
            aria-valuenow={mood}
          />
        </div>

        {/* Mood description */}
        <div className="flex justify-between items-center mt-3">
          <span className="text-xs text-muted-foreground">0</span>
          <span className="text-sm font-medium text-foreground">
            {getMoodEmoji(mood)} {getMoodDescription(mood)}
          </span>
          <span className="text-xs text-muted-foreground">10</span>
        </div>
      </div>

      {/* Sleep */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <label className="block text-foreground mb-2">{t('sleepDuration')}</label>
        <div className="flex items-center space-x-4 mb-4">
          <input
            type="number"
            value={sleepHours}
            onChange={(e) => setSleepHours(Number(e.target.value))}
            min="0"
            max="24"
            step="0.5"
            className="w-20 border border-input bg-background text-foreground rounded-lg px-3 py-2 text-center"
          />
          <span className="text-muted-foreground">{t('hours')}</span>
        </div>

        <label className="block text-foreground mb-2">{t('sleepQuality')}</label>
        <div className="flex space-x-2">
          {sleepLabels.map((label, idx) => (
            <button
              key={idx}
              onClick={() => setSleepQuality(idx + 1)}
              className={`flex-1 py-2 rounded-lg text-sm transition-colors ${sleepQuality === idx + 1
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Medication */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <label className="block text-foreground mb-2">{t('medicationQuestion')}</label>
        <div className="flex space-x-4">
          <button
            onClick={() => setMedication(true)}
            className={`flex-1 py-3 rounded-lg transition-colors ${medication
                ? 'bg-green-500 text-white'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
          >
            ✓ {t('medicationYes')}
          </button>
          <button
            onClick={() => setMedication(false)}
            className={`flex-1 py-3 rounded-lg transition-colors ${!medication
                ? 'bg-red-400 text-white'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
          >
            ✗ {t('medicationNo')}
          </button>
        </div>
      </div>

      {/* Notes */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <label className="block text-foreground mb-2">
          {t('notesLabel')}
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={t('notesPlaceholder')}
          rows={3}
          className="w-full border border-input bg-background text-foreground rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground"
        />
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full bg-blue-500 text-white py-4 rounded-xl text-lg font-semibold disabled:opacity-50 hover:bg-blue-600 transition-all duration-200 flex items-center justify-center gap-2 active:scale-[0.98]"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            {t('submitting')}
          </>
        ) : (
          isEditing ? t('updateButton') : t('submitButton')
        )}
      </button>
    </div>
  );
}
