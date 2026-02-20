'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'
import {
  ArrowLeftIcon,
  Loader2Icon,
  UserPlusIcon,
  CopyIcon,
  CheckIcon,
  EyeIcon,
  EyeOffIcon,
} from '@/components/ui/icons'
import { cn } from '@/lib/utils'
import { locales, localeNames } from '@/i18n/config'

interface FormData {
  email: string
  first_name: string
  last_name: string
  date_of_birth: string
  gender: string
  phone: string
  address: string
  city: string
  country: string
  preferred_language: string
  emergency_contact: string
  emergency_phone: string
  emergency_contact_relationship: string
  current_medications: string
  medical_conditions: string
  allergies: string
  therapy_history: string
  mental_health_goals: string
  support_system: string
  triggers_notes: string
  coping_strategies: string
}

interface CreatedPatient {
  patient_id: string
  user_id: string
  email: string
  full_name: string
  default_password: string
  message: string
}

export default function CreatePatientPage() {
  const router = useRouter()
  const t = useTranslations('doctor.createPatient')
  const common = useTranslations('common')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [createdPatient, setCreatedPatient] = useState<CreatedPatient | null>(null)
  const [copiedPassword, setCopiedPassword] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [activeSection, setActiveSection] = useState<'basic' | 'medical' | 'mental'>('basic')

  const [formData, setFormData] = useState<FormData>({
    email: '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    phone: '',
    address: '',
    city: '',
    country: '',
    preferred_language: '',
    emergency_contact: '',
    emergency_phone: '',
    emergency_contact_relationship: '',
    current_medications: '',
    medical_conditions: '',
    allergies: '',
    therapy_history: '',
    mental_health_goals: '',
    support_system: '',
    triggers_notes: '',
    coping_strategies: '',
  })

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    if (!formData.email.trim()) {
      setError(t('emailRequired'))
      return
    }
    if (!formData.first_name.trim()) {
      setError(t('firstNameRequired'))
      return
    }
    if (!formData.last_name.trim()) {
      setError(t('lastNameRequired'))
      return
    }

    setLoading(true)
    setError('')

    try {
      // Build request data, only including non-empty fields
      const requestData: Record<string, string> = {
        email: formData.email.trim(),
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
      }

      // Add optional fields if they have values
      Object.entries(formData).forEach(([key, value]) => {
        if (value && value.trim() && !['email', 'first_name', 'last_name'].includes(key)) {
          requestData[key] = value.trim()
        }
      })

      const result = await api.createPatient(
        requestData as unknown as Parameters<typeof api.createPatient>[0]
      )
      setCreatedPatient(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('createFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleCopyPassword = async () => {
    if (createdPatient) {
      await navigator.clipboard.writeText(createdPatient.default_password)
      setCopiedPassword(true)
      setTimeout(() => setCopiedPassword(false), 2000)
    }
  }

  const handleCreateAnother = () => {
    setCreatedPatient(null)
    setFormData({
      email: '',
      first_name: '',
      last_name: '',
      date_of_birth: '',
      gender: '',
      phone: '',
      address: '',
      city: '',
      country: '',
      preferred_language: '',
      emergency_contact: '',
      emergency_phone: '',
      emergency_contact_relationship: '',
      current_medications: '',
      medical_conditions: '',
      allergies: '',
      therapy_history: '',
      mental_health_goals: '',
      support_system: '',
      triggers_notes: '',
      coping_strategies: '',
    })
  }

  // Success state - show created patient info
  if (createdPatient) {
    return (
      <div className="max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="bg-card rounded-2xl shadow-sm border border-border p-8">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckIcon className="w-8 h-8 text-success" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">{t('successTitle')}</h2>
            <p className="text-muted-foreground mt-2">{t('successMessage')}</p>
          </div>

          <div className="space-y-4 bg-muted/50 rounded-xl p-6 mb-6">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">{t('patientName')}</span>
              <span className="font-medium text-foreground">{createdPatient.full_name}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">{t('email')}</span>
              <span className="font-medium text-foreground">{createdPatient.email}</span>
            </div>
            <div className="border-t border-border pt-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">{t('defaultPassword')}</span>
                <div className="flex items-center gap-2">
                  <code
                    className={cn(
                      'px-3 py-1 bg-background rounded border border-border font-mono text-sm',
                      !showPassword && 'tracking-widest'
                    )}
                  >
                    {showPassword ? createdPatient.default_password : '••••••••••'}
                  </code>
                  <button
                    onClick={() => setShowPassword(!showPassword)}
                    className="p-1.5 hover:bg-muted rounded-lg transition-colors"
                    title={showPassword ? t('hidePassword') : t('showPassword')}
                  >
                    {showPassword ? (
                      <EyeOffIcon className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <EyeIcon className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>
                  <button
                    onClick={handleCopyPassword}
                    className="p-1.5 hover:bg-muted rounded-lg transition-colors"
                    title={t('copyPassword')}
                  >
                    {copiedPassword ? (
                      <CheckIcon className="w-4 h-4 text-success" />
                    ) : (
                      <CopyIcon className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>
                </div>
              </div>
              <p className="text-xs text-warning mt-2">{t('passwordWarning')}</p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleCreateAnother}
              className="flex-1 px-4 py-2.5 border border-border text-foreground rounded-xl hover:bg-muted transition-colors"
            >
              {t('createAnother')}
            </button>
            <Link
              href={`/patients/${createdPatient.patient_id}`}
              className="flex-1 px-4 py-2.5 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors text-center"
            >
              {t('viewPatient')}
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/patients" className="p-2 hover:bg-muted rounded-lg transition-colors">
          <ArrowLeftIcon className="w-5 h-5 text-muted-foreground" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">{t('title')}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t('subtitle')}</p>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="bg-card rounded-xl border border-border p-1 mb-6 flex gap-1">
        <button
          onClick={() => setActiveSection('basic')}
          className={cn(
            'flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            activeSection === 'basic'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-muted'
          )}
        >
          {t('basicInfo')}
        </button>
        <button
          onClick={() => setActiveSection('medical')}
          className={cn(
            'flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            activeSection === 'medical'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-muted'
          )}
        >
          {t('medicalHistory')}
        </button>
        <button
          onClick={() => setActiveSection('mental')}
          className={cn(
            'flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            activeSection === 'mental'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-muted'
          )}
        >
          {t('mentalHealth')}
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="bg-card rounded-2xl shadow-sm border border-border p-6">
          {/* Basic Information Section */}
          {activeSection === 'basic' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Required fields */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('email')} <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    placeholder="patient@example.com"
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                    required
                  />
                </div>

                <div className="md:col-span-2 grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      {t('firstName')} <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.first_name}
                      onChange={(e) => handleInputChange('first_name', e.target.value)}
                      placeholder={t('firstNamePlaceholder')}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      {t('lastName')} <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.last_name}
                      onChange={(e) => handleInputChange('last_name', e.target.value)}
                      placeholder={t('lastNamePlaceholder')}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                      required
                    />
                  </div>
                </div>

                {/* Optional fields */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('dateOfBirth')}
                  </label>
                  <input
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('gender')}
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  >
                    <option value="">{t('genderSelect')}</option>
                    <option value="male">{t('genderMale')}</option>
                    <option value="female">{t('genderFemale')}</option>
                    <option value="other">{t('genderOther')}</option>
                    <option value="prefer_not_to_say">{t('genderPreferNot')}</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('phone')}
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    placeholder="+1 234 567 8900"
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('preferredLanguage')}
                  </label>
                  <select
                    value={formData.preferred_language}
                    onChange={(e) => handleInputChange('preferred_language', e.target.value)}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  >
                    <option value="">{t('selectLanguage')}</option>
                    {locales.map((loc) => (
                      <option key={loc} value={loc}>
                        {localeNames[loc]}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('address')}
                  </label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    placeholder={t('addressPlaceholder')}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('city')}
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => handleInputChange('city', e.target.value)}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('country')}
                  </label>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) => handleInputChange('country', e.target.value)}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>
              </div>

              {/* Emergency Contact */}
              <div className="border-t border-border pt-6">
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  {t('emergencyContact')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      {t('contactName')}
                    </label>
                    <input
                      type="text"
                      value={formData.emergency_contact}
                      onChange={(e) => handleInputChange('emergency_contact', e.target.value)}
                      placeholder={t('contactNamePlaceholder')}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      {t('contactPhone')}
                    </label>
                    <input
                      type="tel"
                      value={formData.emergency_phone}
                      onChange={(e) => handleInputChange('emergency_phone', e.target.value)}
                      placeholder={t('contactPhonePlaceholder')}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      {t('relationship')}
                    </label>
                    <input
                      type="text"
                      value={formData.emergency_contact_relationship}
                      onChange={(e) =>
                        handleInputChange('emergency_contact_relationship', e.target.value)
                      }
                      placeholder={t('relationshipPlaceholder')}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Medical History Section */}
          {activeSection === 'medical' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('currentMedications')}
                </label>
                <textarea
                  value={formData.current_medications}
                  onChange={(e) => handleInputChange('current_medications', e.target.value)}
                  placeholder={t('medicationsPlaceholder')}
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('medicalConditions')}
                </label>
                <textarea
                  value={formData.medical_conditions}
                  onChange={(e) => handleInputChange('medical_conditions', e.target.value)}
                  placeholder={t('conditionsPlaceholder')}
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('allergies')}
                </label>
                <textarea
                  value={formData.allergies}
                  onChange={(e) => handleInputChange('allergies', e.target.value)}
                  placeholder={t('allergiesPlaceholder')}
                  rows={2}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('therapyHistory')}
                </label>
                <textarea
                  value={formData.therapy_history}
                  onChange={(e) => handleInputChange('therapy_history', e.target.value)}
                  placeholder={t('therapyPlaceholder')}
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>
            </div>
          )}

          {/* Mental Health Section */}
          {activeSection === 'mental' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('mentalHealthGoals')}
                </label>
                <textarea
                  value={formData.mental_health_goals}
                  onChange={(e) => handleInputChange('mental_health_goals', e.target.value)}
                  placeholder={t('goalsPlaceholder')}
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('supportSystem')}
                </label>
                <textarea
                  value={formData.support_system}
                  onChange={(e) => handleInputChange('support_system', e.target.value)}
                  placeholder={t('supportPlaceholder')}
                  rows={2}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('knownTriggers')}
                </label>
                <textarea
                  value={formData.triggers_notes}
                  onChange={(e) => handleInputChange('triggers_notes', e.target.value)}
                  placeholder={t('triggersPlaceholder')}
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('copingStrategies')}
                </label>
                <textarea
                  value={formData.coping_strategies}
                  onChange={(e) => handleInputChange('coping_strategies', e.target.value)}
                  placeholder={t('copingPlaceholder')}
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="mt-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="mt-8 flex gap-4">
            <Link
              href="/patients"
              className="px-6 py-2.5 border border-border text-muted-foreground rounded-xl hover:bg-muted transition-colors"
            >
              {common('cancel')}
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-2.5 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2Icon className="w-4 h-4 animate-spin" />
                  {t('creating')}
                </>
              ) : (
                <>
                  <UserPlusIcon className="w-4 h-4" />
                  {t('createPatient')}
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
