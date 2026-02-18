'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'
import {
  UserIcon,
  PhoneIcon,
  BuildingIcon,
  MapPinIcon,
  ClockIcon,
  GraduationCapIcon,
  LanguagesIcon,
  FileTextIcon,
  BriefcaseIcon,
  SaveIcon,
  Loader2Icon,
  ShieldIcon,
} from '@/components/ui/icons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Disclosure, DisclosureButton, DisclosurePanel } from '@/components/ui/disclosure'

interface DoctorProfile {
  id: string
  user_id: string
  first_name: string
  last_name: string
  full_name?: string
  license_number?: string
  specialty?: string
  created_at: string
  updated_at?: string
  phone?: string
  bio?: string
  years_of_experience?: string
  education?: string
  languages?: string
  clinic_name?: string
  clinic_address?: string
  clinic_city?: string
  clinic_country?: string
  consultation_hours?: string
}

export default function DoctorProfilePage() {
  const t = useTranslations('doctor.profile')
  const common = useTranslations('common')

  const [profile, setProfile] = useState<DoctorProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const [formData, setFormData] = useState<Partial<DoctorProfile>>({})

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await api.getDoctorProfile()
        setProfile(data)
        setFormData(data)
      } catch (err) {
        console.error('Error fetching profile:', err)
        setError(common('error'))
      } finally {
        setLoading(false)
      }
    }
    fetchProfile()
  }, [common])

  const handleChange = (field: keyof DoctorProfile, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setSuccess(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess(false)

    try {
      const updatedProfile = await api.updateDoctorProfile(formData)
      setProfile(updatedProfile)
      setSuccess(true)
    } catch (err) {
      console.error('Error saving profile:', err)
      setError(t('saveError', { defaultValue: 'Failed to save profile' }))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <Loader2Icon className="w-8 h-8 text-primary animate-spin mb-3" />
        <p className="text-muted-foreground text-sm">{common('loading')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="flex justify-between items-center bg-card p-4 rounded-xl border border-border shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-foreground">
            {t('title', { defaultValue: 'My Profile' })}
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            {t('subtitle', { defaultValue: 'Manage your professional profile' })}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
        {/* Success Message */}
        {success && (
          <div className="p-3 bg-success/10 text-success text-sm rounded-lg flex items-center">
            <ShieldIcon className="w-4 h-4 mr-2" />
            {t('saveSuccess', { defaultValue: 'Profile saved successfully' })}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-lg">{error}</div>
        )}

        {/* Personal Information */}
        <Disclosure defaultOpen>
          <DisclosureButton className="w-full">
            <div className="flex items-center">
              <UserIcon className="w-5 h-5 mr-2 text-primary" />
              <span className="font-medium">
                {t('personalInfo', { defaultValue: 'Personal Information' })}
              </span>
            </div>
          </DisclosureButton>
          <DisclosurePanel>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('firstName', { defaultValue: 'First Name' })}
                  </label>
                  <Input
                    value={formData.first_name || ''}
                    onChange={(e) => handleChange('first_name', e.target.value)}
                    placeholder={t('firstNamePlaceholder', { defaultValue: 'John' })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('lastName', { defaultValue: 'Last Name' })}
                  </label>
                  <Input
                    value={formData.last_name || ''}
                    onChange={(e) => handleChange('last_name', e.target.value)}
                    placeholder={t('lastNamePlaceholder', { defaultValue: 'Smith' })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('specialty', { defaultValue: 'Specialty' })}
                  </label>
                  <Input
                    value={formData.specialty || ''}
                    onChange={(e) => handleChange('specialty', e.target.value)}
                    placeholder={t('specialtyPlaceholder', { defaultValue: 'Psychiatry' })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('licenseNumber', { defaultValue: 'License Number' })}
                  </label>
                  <Input
                    value={formData.license_number || ''}
                    onChange={(e) => handleChange('license_number', e.target.value)}
                    placeholder={t('licensePlaceholder', { defaultValue: 'MD12345' })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <PhoneIcon className="w-4 h-4 inline mr-1" />
                  {t('phone', { defaultValue: 'Phone Number' })}
                </label>
                <Input
                  type="tel"
                  value={formData.phone || ''}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  placeholder={t('phonePlaceholder', { defaultValue: '+1 (555) 123-4567' })}
                />
              </div>
            </div>
          </DisclosurePanel>
        </Disclosure>

        {/* Professional Background */}
        <Disclosure defaultOpen>
          <DisclosureButton className="w-full">
            <div className="flex items-center">
              <BriefcaseIcon className="w-5 h-5 mr-2 text-primary" />
              <span className="font-medium">
                {t('professionalBackground', { defaultValue: 'Professional Background' })}
              </span>
            </div>
          </DisclosureButton>
          <DisclosurePanel>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <FileTextIcon className="w-4 h-4 inline mr-1" />
                  {t('bio', { defaultValue: 'Professional Bio' })}
                </label>
                <textarea
                  value={formData.bio || ''}
                  onChange={(e) => handleChange('bio', e.target.value)}
                  placeholder={t('bioPlaceholder', {
                    defaultValue: 'Brief description of your background and approach...',
                  })}
                  rows={4}
                  className="w-full px-3 py-2 bg-background border border-input rounded-xl text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring transition-all resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    <ClockIcon className="w-4 h-4 inline mr-1" />
                    {t('yearsExperience', { defaultValue: 'Years of Experience' })}
                  </label>
                  <Input
                    value={formData.years_of_experience || ''}
                    onChange={(e) => handleChange('years_of_experience', e.target.value)}
                    placeholder={t('yearsPlaceholder', { defaultValue: '10+' })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    <LanguagesIcon className="w-4 h-4 inline mr-1" />
                    {t('languages', { defaultValue: 'Languages' })}
                  </label>
                  <Input
                    value={formData.languages || ''}
                    onChange={(e) => handleChange('languages', e.target.value)}
                    placeholder={t('languagesPlaceholder', { defaultValue: 'English, Mandarin' })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <GraduationCapIcon className="w-4 h-4 inline mr-1" />
                  {t('education', { defaultValue: 'Education & Qualifications' })}
                </label>
                <textarea
                  value={formData.education || ''}
                  onChange={(e) => handleChange('education', e.target.value)}
                  placeholder={t('educationPlaceholder', {
                    defaultValue: 'Medical school, residency, certifications...',
                  })}
                  rows={3}
                  className="w-full px-3 py-2 bg-background border border-input rounded-xl text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring transition-all resize-none"
                />
              </div>
            </div>
          </DisclosurePanel>
        </Disclosure>

        {/* Clinic Information */}
        <Disclosure defaultOpen>
          <DisclosureButton className="w-full">
            <div className="flex items-center">
              <BuildingIcon className="w-5 h-5 mr-2 text-primary" />
              <span className="font-medium">
                {t('clinicInfo', { defaultValue: 'Clinic Information' })}
              </span>
            </div>
          </DisclosureButton>
          <DisclosurePanel>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('clinicName', { defaultValue: 'Clinic/Hospital Name' })}
                </label>
                <Input
                  value={formData.clinic_name || ''}
                  onChange={(e) => handleChange('clinic_name', e.target.value)}
                  placeholder={t('clinicNamePlaceholder', {
                    defaultValue: 'City Mental Health Center',
                  })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <MapPinIcon className="w-4 h-4 inline mr-1" />
                  {t('clinicAddress', { defaultValue: 'Address' })}
                </label>
                <Input
                  value={formData.clinic_address || ''}
                  onChange={(e) => handleChange('clinic_address', e.target.value)}
                  placeholder={t('addressPlaceholder', { defaultValue: '123 Medical Center Dr' })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('city', { defaultValue: 'City' })}
                  </label>
                  <Input
                    value={formData.clinic_city || ''}
                    onChange={(e) => handleChange('clinic_city', e.target.value)}
                    placeholder={t('cityPlaceholder', { defaultValue: 'Toronto' })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('country', { defaultValue: 'Country' })}
                  </label>
                  <Input
                    value={formData.clinic_country || ''}
                    onChange={(e) => handleChange('clinic_country', e.target.value)}
                    placeholder={t('countryPlaceholder', { defaultValue: 'Canada' })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <ClockIcon className="w-4 h-4 inline mr-1" />
                  {t('consultationHours', { defaultValue: 'Consultation Hours' })}
                </label>
                <Input
                  value={formData.consultation_hours || ''}
                  onChange={(e) => handleChange('consultation_hours', e.target.value)}
                  placeholder={t('hoursPlaceholder', { defaultValue: 'Mon-Fri 9:00 AM - 5:00 PM' })}
                />
              </div>
            </div>
          </DisclosurePanel>
        </Disclosure>

        {/* Save Button */}
        <Button type="submit" disabled={saving} className="w-full">
          {saving ? (
            <>
              <Loader2Icon className="w-5 h-5 mr-2 animate-spin" />
              {t('saving', { defaultValue: 'Saving...' })}
            </>
          ) : (
            <>
              <SaveIcon className="w-5 h-5 mr-2" />
              {t('saveProfile', { defaultValue: 'Save Profile' })}
            </>
          )}
        </Button>
      </form>
    </div>
  )
}
