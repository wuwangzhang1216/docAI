'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import {
  UserIcon,
  PhoneIcon,
  CalendarIcon,
  MapPinIcon,
  PillIcon,
  HeartIcon,
  AlertCircleIcon,
  TargetIcon,
  UsersIcon,
  MessageSquareIcon,
  SparklesIcon,
} from '@/components/ui/icons';
import Link from 'next/link';
import { Disclosure, DisclosureButton, DisclosurePanel } from '@/components/ui/disclosure';
import ReportGenerator from '@/components/doctor/ReportGenerator';

interface Checkin {
  id: string;
  checkin_date: string;
  mood_score: number;
  sleep_hours: number;
  sleep_quality: number;
  medication_taken: boolean;
  notes?: string;
}

interface PatientProfile {
  id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  date_of_birth?: string;
  phone?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  emergency_contact_relationship?: string;
  gender?: string;
  address?: string;
  city?: string;
  country?: string;
  current_medications?: string;
  medical_conditions?: string;
  allergies?: string;
  therapy_history?: string;
  mental_health_goals?: string;
  support_system?: string;
  triggers_notes?: string;
  coping_strategies?: string;
}

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = params.id as string;
  const t = useTranslations('doctor.patientDetail');
  const common = useTranslations('common');

  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [checkins, setCheckins] = useState<Checkin[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch profile and checkins in parallel
        const endDate = new Date().toISOString().split('T')[0];
        const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0];

        const [profileData, checkinsData] = await Promise.all([
          api.getPatientProfile(patientId),
          api.getPatientCheckins(patientId, startDate, endDate),
        ]);

        setProfile(profileData);
        setCheckins(checkinsData);
      } catch (error) {
        console.error('Error fetching patient data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [patientId]);

  const calculateAge = (dob: string) => {
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const getMoodEmoji = (score: number) => {
    if (score <= 2) return '😢';
    if (score <= 4) return '😔';
    if (score <= 6) return '😐';
    if (score <= 8) return '🙂';
    return '😊';
  };

  const getSleepQualityLabel = (quality: number) => {
    const labels = t.raw('sleepLabels') as string[];
    return labels[quality] || '-';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => router.back()}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            ← {common('back')}
          </button>
          <h2 className="text-xl font-bold text-foreground">{t('title')}</h2>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={`/patients/${patientId}/ai-assistant`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium text-sm"
          >
            <SparklesIcon className="w-4 h-4" />
            {t('aiAssistant', { defaultValue: 'AI Assistant' })}
          </Link>
          <Link
            href={`/doctor-messages?patient=${patientId}`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors font-medium text-sm"
          >
            <MessageSquareIcon className="w-4 h-4" />
            {t('sendMessage', { defaultValue: 'Send Message' })}
          </Link>
        </div>
      </div>

      {/* Patient Profile Header */}
      {profile && (
        <div className="bg-primary rounded-xl p-6 text-primary-foreground">
          <div className="flex items-center gap-4">
            <div className="bg-primary-foreground/20 p-3 rounded-full">
              <UserIcon className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">{profile.first_name} {profile.last_name}</h2>
              <div className="flex items-center gap-4 text-primary-foreground/80 text-sm mt-1">
                {profile.date_of_birth && (
                  <span className="flex items-center gap-1">
                    <CalendarIcon className="w-4 h-4" />
                    {calculateAge(profile.date_of_birth)} {t('yearsOld', { defaultValue: 'years old' })}
                  </span>
                )}
                {profile.gender && <span>{profile.gender}</span>}
                {profile.phone && (
                  <span className="flex items-center gap-1">
                    <PhoneIcon className="w-4 h-4" />
                    {profile.phone}
                  </span>
                )}
              </div>
              {profile.city && (
                <p className="text-primary-foreground/80 text-sm mt-1 flex items-center gap-1">
                  <MapPinIcon className="w-4 h-4" />
                  {profile.city}, ON
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Emergency Contact */}
      {profile && (profile.emergency_contact || profile.emergency_phone) && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-400 font-medium mb-2">
            <PhoneIcon className="w-4 h-4" />
            {t('emergencyContact', { defaultValue: 'Emergency Contact' })}
          </div>
          <p className="text-red-800 dark:text-red-300">
            {profile.emergency_contact}
            {profile.emergency_contact_relationship && ` (${profile.emergency_contact_relationship})`}
            {profile.emergency_phone && ` - ${profile.emergency_phone}`}
          </p>
        </div>
      )}

      {/* Medical Information */}
      {profile && (profile.current_medications || profile.medical_conditions || profile.allergies) && (
        <Disclosure defaultOpen={true}>
          <DisclosureButton>
            <div className="flex items-center gap-3">
              <div className="bg-green-500/10 p-2 rounded-lg">
                <PillIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <span className="font-semibold text-foreground">{t('medicalInfo', { defaultValue: 'Medical Information' })}</span>
            </div>
          </DisclosureButton>

          <DisclosurePanel className="space-y-4 border-t border-border">
            {profile.current_medications && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-1">{t('medications', { defaultValue: 'Current Medications' })}</h4>
                <p className="text-muted-foreground bg-muted p-3 rounded-lg whitespace-pre-wrap">{profile.current_medications}</p>
              </div>
            )}
            {profile.medical_conditions && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-1">{t('conditions', { defaultValue: 'Medical Conditions' })}</h4>
                <p className="text-muted-foreground bg-muted p-3 rounded-lg whitespace-pre-wrap">{profile.medical_conditions}</p>
              </div>
            )}
            {profile.allergies && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-1 flex items-center gap-1">
                  <AlertCircleIcon className="w-4 h-4 text-red-500 dark:text-red-400" />
                  {t('allergies', { defaultValue: 'Allergies' })}
                </h4>
                <p className="text-muted-foreground bg-red-500/10 p-3 rounded-lg whitespace-pre-wrap">{profile.allergies}</p>
              </div>
            )}
          </DisclosurePanel>
        </Disclosure>
      )}

      {/* Mental Health Context */}
      {profile && (profile.therapy_history || profile.mental_health_goals || profile.support_system || profile.triggers_notes || profile.coping_strategies) && (
        <Disclosure defaultOpen={true}>
          <DisclosureButton>
            <div className="flex items-center gap-3">
              <div className="bg-purple-500/10 p-2 rounded-lg">
                <HeartIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <span className="font-semibold text-foreground">{t('mentalHealthContext', { defaultValue: 'Mental Health Context' })}</span>
            </div>
          </DisclosureButton>

          <DisclosurePanel className="space-y-4 border-t border-border">
            {profile.therapy_history && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-1">{t('therapyHistory', { defaultValue: 'Therapy History' })}</h4>
                <p className="text-muted-foreground bg-muted p-3 rounded-lg whitespace-pre-wrap">{profile.therapy_history}</p>
              </div>
            )}
            {profile.mental_health_goals && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-1 flex items-center gap-1">
                  <TargetIcon className="w-4 h-4 text-blue-500 dark:text-blue-400" />
                  {t('goals', { defaultValue: 'Mental Health Goals' })}
                </h4>
                <p className="text-muted-foreground bg-blue-500/10 p-3 rounded-lg whitespace-pre-wrap">{profile.mental_health_goals}</p>
              </div>
            )}
            {profile.support_system && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-1 flex items-center gap-1">
                  <UsersIcon className="w-4 h-4 text-green-500 dark:text-green-400" />
                  {t('supportSystem', { defaultValue: 'Support System' })}
                </h4>
                <p className="text-muted-foreground bg-green-500/10 p-3 rounded-lg whitespace-pre-wrap">{profile.support_system}</p>
              </div>
            )}
            {profile.triggers_notes && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-1">{t('triggers', { defaultValue: 'Known Triggers' })}</h4>
                <p className="text-muted-foreground bg-orange-500/10 p-3 rounded-lg whitespace-pre-wrap">{profile.triggers_notes}</p>
              </div>
            )}
            {profile.coping_strategies && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-1">{t('copingStrategies', { defaultValue: 'Coping Strategies' })}</h4>
                <p className="text-muted-foreground bg-muted p-3 rounded-lg whitespace-pre-wrap">{profile.coping_strategies}</p>
              </div>
            )}
          </DisclosurePanel>
        </Disclosure>
      )}

      {/* Report Generator */}
      {profile && (
        <ReportGenerator
          patientId={patientId}
          patientName={`${profile.first_name} ${profile.last_name}`}
        />
      )}

      {/* Mood Chart */}
      <Disclosure defaultOpen={true}>
        <DisclosureButton>
          <span className="font-semibold text-foreground">{t('moodTrend')}</span>
        </DisclosureButton>

        <DisclosurePanel className="border-t border-border">
          {checkins.length > 0 ? (
            <div className="flex items-end space-x-1 h-32 mt-4">
              {checkins.map((c) => (
                <div
                  key={c.id}
                  className="flex-1 bg-primary/30 rounded-t hover:bg-primary/40 transition-colors relative group"
                  style={{ height: `${(c.mood_score / 10) * 100}%` }}
                >
                  <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-foreground text-background text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    {c.checkin_date}: {c.mood_score}{t('score')}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">{t('noCheckinData')}</p>
          )}
        </DisclosurePanel>
      </Disclosure>

      {/* Checkin History */}
      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-border bg-muted/50">
          <h3 className="font-medium text-foreground">{t('checkinHistory')}</h3>
        </div>
        {checkins.length > 0 ? (
          <div className="divide-y divide-border">
            {checkins.slice().reverse().map((c) => (
              <div key={c.id} className="px-4 py-3">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-foreground">{c.checkin_date}</p>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground mt-1">
                      <span>
                        {t('mood')}: {getMoodEmoji(c.mood_score)} {c.mood_score}/10
                      </span>
                      <span>{t('sleep')}: {c.sleep_hours}h</span>
                      <span>{t('quality')}: {getSleepQualityLabel(c.sleep_quality)}</span>
                      <span>
                        {t('medication')}:{' '}
                        {c.medication_taken ? (
                          <span className="text-green-500 dark:text-green-400">✓</span>
                        ) : (
                          <span className="text-red-500 dark:text-red-400">✗</span>
                        )}
                      </span>
                    </div>
                    {c.notes && (
                      <p className="text-sm text-muted-foreground mt-2 bg-muted p-2 rounded">
                        {c.notes}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground text-center py-8">{t('noCheckinRecords')}</p>
        )}
      </div>
    </div>
  );
}
