'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'
import {
  User,
  Phone,
  Calendar,
  MapPin,
  Heart,
  Pill,
  AlertCircle,
  Target,
  Users,
  Shield,
  Save,
  Loader2,
  Stethoscope,
  UserCheck,
  UserX,
  Bell,
  X,
  Check,
  Eye,
  Building,
  Clock,
  GraduationCap,
  Languages,
  Download,
  ChevronRight,
} from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, type SelectOption } from '@/components/ui/select'
import { Disclosure, DisclosureButton, DisclosurePanel } from '@/components/ui/disclosure'
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from '@/components/ui/dialog'

interface PatientProfile {
  id: string
  first_name: string
  last_name: string
  full_name?: string
  date_of_birth?: string
  phone?: string
  emergency_contact?: string
  emergency_phone?: string
  emergency_contact_relationship?: string
  gender?: string
  preferred_language?: string
  address?: string
  city?: string
  country?: string
  current_medications?: string
  medical_conditions?: string
  allergies?: string
  therapy_history?: string
  mental_health_goals?: string
  support_system?: string
  triggers_notes?: string
  coping_strategies?: string
}

interface DoctorInfo {
  id: string
  full_name: string
  specialty?: string
}

interface DoctorFullProfile {
  id: string
  first_name: string
  last_name: string
  full_name?: string
  specialty?: string
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

interface ConnectionRequest {
  id: string
  doctor_id: string
  doctor_name: string
  doctor_specialty?: string
  message?: string
  created_at: string
}

export default function ProfilePage() {
  const t = useTranslations('patient.profile')
  const tDataExport = useTranslations('patient.dataExport')
  const common = useTranslations('common')

  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  // Form state
  const [formData, setFormData] = useState<Partial<PatientProfile>>({})

  // Doctor connection state
  const [myDoctor, setMyDoctor] = useState<DoctorInfo | null>(null)
  const [doctorProfile, setDoctorProfile] = useState<DoctorFullProfile | null>(null)
  const [connectionRequests, setConnectionRequests] = useState<ConnectionRequest[]>([])
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false)
  const [showDoctorProfileDialog, setShowDoctorProfileDialog] = useState(false)
  const [loadingDoctorProfile, setLoadingDoctorProfile] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)
  const [processingRequestId, setProcessingRequestId] = useState<string | null>(null)

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await api.getMyProfile()
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

  useEffect(() => {
    const fetchDoctorData = async () => {
      try {
        const [doctor, requests] = await Promise.all([
          api.getMyDoctor(),
          api.getMyConnectionRequests(),
        ])
        setMyDoctor(doctor)
        setConnectionRequests(requests)
      } catch (err) {
        console.error('Error fetching doctor data:', err)
      }
    }
    fetchDoctorData()
  }, [])

  const handleAcceptRequest = async (requestId: string) => {
    setProcessingRequestId(requestId)
    try {
      await api.acceptConnectionRequest(requestId)
      const doctor = await api.getMyDoctor()
      setMyDoctor(doctor)
      setConnectionRequests((prev) => prev.filter((r) => r.id !== requestId))
    } catch (err) {
      console.error('Error accepting request:', err)
      alert(common('error'))
    } finally {
      setProcessingRequestId(null)
    }
  }

  const handleRejectRequest = async (requestId: string) => {
    setProcessingRequestId(requestId)
    try {
      await api.rejectConnectionRequest(requestId)
      setConnectionRequests((prev) => prev.filter((r) => r.id !== requestId))
    } catch (err) {
      console.error('Error rejecting request:', err)
      alert(common('error'))
    } finally {
      setProcessingRequestId(null)
    }
  }

  const handleDisconnect = async () => {
    setDisconnecting(true)
    try {
      await api.disconnectFromDoctor()
      setMyDoctor(null)
      setShowDisconnectDialog(false)
    } catch (err) {
      console.error('Error disconnecting:', err)
      alert(common('error'))
    } finally {
      setDisconnecting(false)
    }
  }

  const handleViewDoctorProfile = async () => {
    setLoadingDoctorProfile(true)
    setShowDoctorProfileDialog(true)
    try {
      const profile = await api.getMyDoctorProfile()
      setDoctorProfile(profile)
    } catch (err) {
      console.error('Error fetching doctor profile:', err)
    } finally {
      setLoadingDoctorProfile(false)
    }
  }

  const handleChange = (field: keyof PatientProfile, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setSuccess(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess(false)

    try {
      const updated = await api.updateMyProfile(formData)
      setProfile(updated)
      setSuccess(true)
    } catch (err) {
      console.error('Error updating profile:', err)
      setError(common('error'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  const genderOptions: SelectOption[] = [
    { value: 'male', label: t('genderMale', { defaultValue: 'Male' }) },
    { value: 'female', label: t('genderFemale', { defaultValue: 'Female' }) },
    { value: 'non_binary', label: t('genderNonBinary', { defaultValue: 'Non-binary' }) },
    { value: 'other', label: t('genderOther', { defaultValue: 'Other' }) },
    { value: 'prefer_not_say', label: t('genderPreferNot', { defaultValue: 'Prefer not to say' }) },
  ]

  const relationshipOptions: SelectOption[] = [
    { value: 'spouse', label: t('relationshipSpouse', { defaultValue: 'Spouse/Partner' }) },
    { value: 'parent', label: t('relationshipParent', { defaultValue: 'Parent' }) },
    { value: 'sibling', label: t('relationshipSibling', { defaultValue: 'Sibling' }) },
    { value: 'child', label: t('relationshipChild', { defaultValue: 'Child' }) },
    { value: 'friend', label: t('relationshipFriend', { defaultValue: 'Friend' }) },
    { value: 'other', label: t('relationshipOther', { defaultValue: 'Other' }) },
  ]

  return (
    <div className="p-4">
      <div className="space-y-4 max-w-2xl mx-auto pb-20 md:pb-8">
        <h1 className="text-xl font-bold mb-4">{t('title', { defaultValue: 'My Profile' })}</h1>

        {/* Connection Requests Section */}
        {connectionRequests.length > 0 && (
          <div className="bg-warning/10 border border-warning/20 rounded-xl p-4 mb-4">
            <div className="flex items-center gap-2 mb-3">
              <Bell className="w-5 h-5 text-warning" />
              <h2 className="font-semibold text-warning">
                {t('connectionRequests.title', { defaultValue: 'Connection Requests' })}
              </h2>
              <span className="bg-warning text-warning-foreground text-xs px-2 py-0.5 rounded-full">
                {connectionRequests.length}
              </span>
            </div>
            <p className="text-sm text-warning mb-3">
              {t('connectionRequests.description', {
                defaultValue: 'A doctor wants to connect with you to provide care.',
              })}
            </p>
            <div className="space-y-3">
              {connectionRequests.map((request) => (
                <div key={request.id} className="bg-card rounded-lg p-3 border border-border">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
                        {request.doctor_name[0]}
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{request.doctor_name}</p>
                        {request.doctor_specialty && (
                          <p className="text-sm text-muted-foreground">
                            {request.doctor_specialty}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  {request.message && (
                    <p className="text-sm text-muted-foreground mt-2 bg-muted p-2 rounded">
                      &ldquo;{request.message}&rdquo;
                    </p>
                  )}
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => handleAcceptRequest(request.id)}
                      disabled={processingRequestId === request.id}
                      className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-success text-success-foreground rounded-lg hover:bg-success/90 disabled:opacity-50 text-sm font-medium"
                    >
                      {processingRequestId === request.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Check className="w-4 h-4" />
                          {t('connectionRequests.accept', { defaultValue: 'Accept' })}
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleRejectRequest(request.id)}
                      disabled={processingRequestId === request.id}
                      className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-border text-muted-foreground rounded-lg hover:bg-muted disabled:opacity-50 text-sm font-medium"
                    >
                      <X className="w-4 h-4" />
                      {t('connectionRequests.reject', { defaultValue: 'Reject' })}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* My Doctor Section */}
        <div className="bg-card border border-border rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Stethoscope className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h2 className="font-semibold text-foreground">
              {t('myDoctor.title', { defaultValue: 'My Doctor' })}
            </h2>
          </div>

          {myDoctor ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-lg">
                  {myDoctor.full_name[0]}
                </div>
                <div>
                  <p className="font-medium text-foreground">{myDoctor.full_name}</p>
                  {myDoctor.specialty && (
                    <p className="text-sm text-muted-foreground">{myDoctor.specialty}</p>
                  )}
                  <div className="flex items-center gap-1 text-xs text-success mt-1">
                    <UserCheck className="w-3 h-3" />
                    {t('myDoctor.connected', { defaultValue: 'Connected' })}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleViewDoctorProfile}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                >
                  <Eye className="w-4 h-4" />
                  {t('myDoctor.viewProfile', { defaultValue: 'View Profile' })}
                </button>
                <button
                  onClick={() => setShowDisconnectDialog(true)}
                  className="px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
                >
                  {t('myDoctor.disconnect', { defaultValue: 'Disconnect' })}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 text-muted-foreground">
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <UserX className="w-6 h-6 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm">
                  {t('myDoctor.noDoctor', { defaultValue: 'No doctor connected' })}
                </p>
                <p className="text-xs text-muted-foreground">
                  {t('myDoctor.noDoctorHint', {
                    defaultValue: 'Your doctor will send you a connection request',
                  })}
                </p>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Success Message */}
          {success && (
            <div className="p-3 bg-success/10 text-success text-sm rounded-lg flex items-center">
              <Shield className="w-4 h-4 mr-2" />
              {t('saveSuccess', { defaultValue: 'Profile updated successfully!' })}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              {error}
            </div>
          )}

          {/* Personal Information */}
          <Disclosure defaultOpen={true}>
            <DisclosureButton>
              <div className="flex items-center gap-3">
                <div className="bg-blue-500/10 p-2 rounded-lg">
                  <User className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <span className="font-semibold">
                  {t('personalInfo', { defaultValue: 'Personal Information' })}
                </span>
              </div>
            </DisclosureButton>

            <DisclosurePanel className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('firstName', { defaultValue: 'First Name' })}
                  </label>
                  <Input
                    value={formData.first_name || ''}
                    onChange={(e) => handleChange('first_name', e.target.value)}
                    placeholder={t('firstNamePlaceholder', { defaultValue: 'First name' })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('lastName', { defaultValue: 'Last Name' })}
                  </label>
                  <Input
                    value={formData.last_name || ''}
                    onChange={(e) => handleChange('last_name', e.target.value)}
                    placeholder={t('lastNamePlaceholder', { defaultValue: 'Last name' })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    <Calendar className="w-4 h-4 inline mr-1" />
                    {t('dateOfBirth', { defaultValue: 'Date of Birth' })}
                  </label>
                  <Input
                    type="date"
                    value={formData.date_of_birth || ''}
                    onChange={(e) => handleChange('date_of_birth', e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('gender', { defaultValue: 'Gender' })}
                  </label>
                  <Select
                    value={formData.gender || ''}
                    onChange={(value) => handleChange('gender', value)}
                    options={genderOptions}
                    placeholder={t('genderSelect', { defaultValue: 'Select...' })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <Phone className="w-4 h-4 inline mr-1" />
                  {t('phone', { defaultValue: 'Phone Number' })}
                </label>
                <Input
                  type="tel"
                  value={formData.phone || ''}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <MapPin className="w-4 h-4 inline mr-1" />
                  {t('address', { defaultValue: 'Address' })}
                </label>
                <Input
                  value={formData.address || ''}
                  onChange={(e) => handleChange('address', e.target.value)}
                  placeholder={t('addressPlaceholder', { defaultValue: 'Street address' })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('city', { defaultValue: 'City' })}
                </label>
                <Input
                  value={formData.city || ''}
                  onChange={(e) => handleChange('city', e.target.value)}
                  placeholder="Toronto"
                />
                <p className="text-xs text-muted-foreground mt-1">Ontario, Canada</p>
              </div>
            </DisclosurePanel>
          </Disclosure>

          {/* Emergency Contact */}
          <Disclosure defaultOpen={false}>
            <DisclosureButton>
              <div className="flex items-center gap-3">
                <div className="bg-red-500/10 p-2 rounded-lg">
                  <Phone className="w-5 h-5 text-red-600 dark:text-red-400" />
                </div>
                <span className="font-semibold">
                  {t('emergencyContact', { defaultValue: 'Emergency Contact' })}
                </span>
              </div>
            </DisclosureButton>

            <DisclosurePanel className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('emergencyName', { defaultValue: 'Contact Name' })}
                </label>
                <Input
                  value={formData.emergency_contact || ''}
                  onChange={(e) => handleChange('emergency_contact', e.target.value)}
                  placeholder={t('emergencyNamePlaceholder', {
                    defaultValue: 'Name of emergency contact',
                  })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('emergencyPhone', { defaultValue: 'Phone' })}
                  </label>
                  <Input
                    type="tel"
                    value={formData.emergency_phone || ''}
                    onChange={(e) => handleChange('emergency_phone', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    {t('relationship', { defaultValue: 'Relationship' })}
                  </label>
                  <Select
                    value={formData.emergency_contact_relationship || ''}
                    onChange={(value) => handleChange('emergency_contact_relationship', value)}
                    options={relationshipOptions}
                    placeholder={t('relationshipSelect', { defaultValue: 'Select...' })}
                  />
                </div>
              </div>
            </DisclosurePanel>
          </Disclosure>

          {/* Medical Information */}
          <Disclosure defaultOpen={false}>
            <DisclosureButton>
              <div className="flex items-center gap-3">
                <div className="bg-emerald-500/10 p-2 rounded-lg">
                  <Pill className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <span className="font-semibold">
                  {t('medicalInfo', { defaultValue: 'Medical Information' })}
                </span>
              </div>
            </DisclosureButton>

            <DisclosurePanel className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('currentMedications', { defaultValue: 'Current Medications' })}
                </label>
                <textarea
                  value={formData.current_medications || ''}
                  onChange={(e) => handleChange('current_medications', e.target.value)}
                  placeholder={t('medicationsPlaceholder', {
                    defaultValue: 'List any medications you are currently taking...',
                  })}
                  rows={3}
                  className="w-full border border-input bg-background text-foreground rounded-xl px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('medicalConditions', { defaultValue: 'Medical Conditions' })}
                </label>
                <textarea
                  value={formData.medical_conditions || ''}
                  onChange={(e) => handleChange('medical_conditions', e.target.value)}
                  placeholder={t('conditionsPlaceholder', {
                    defaultValue: 'Any relevant medical conditions...',
                  })}
                  rows={3}
                  className="w-full border border-input bg-background text-foreground rounded-xl px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <AlertCircle className="w-4 h-4 inline mr-1" />
                  {t('allergies', { defaultValue: 'Allergies' })}
                </label>
                <textarea
                  value={formData.allergies || ''}
                  onChange={(e) => handleChange('allergies', e.target.value)}
                  placeholder={t('allergiesPlaceholder', { defaultValue: 'List any allergies...' })}
                  rows={2}
                  className="w-full border border-input bg-background text-foreground rounded-xl px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </DisclosurePanel>
          </Disclosure>

          {/* Mental Health Information */}
          <Disclosure defaultOpen={false}>
            <DisclosureButton>
              <div className="flex items-center gap-3">
                <div className="bg-purple-500/10 p-2 rounded-lg">
                  <Heart className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <span className="font-semibold">
                  {t('mentalHealthInfo', { defaultValue: 'Mental Health Context' })}
                </span>
              </div>
            </DisclosureButton>

            <DisclosurePanel className="space-y-4">
              <p className="text-sm text-muted-foreground mb-4">
                {t('mentalHealthNote', {
                  defaultValue:
                    'This information helps your healthcare provider better understand your needs. All information is confidential.',
                })}
              </p>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('therapyHistory', { defaultValue: 'Therapy History' })}
                </label>
                <textarea
                  value={formData.therapy_history || ''}
                  onChange={(e) => handleChange('therapy_history', e.target.value)}
                  placeholder={t('therapyHistoryPlaceholder', {
                    defaultValue: 'Previous therapy or counseling experience...',
                  })}
                  rows={3}
                  className="w-full border border-input bg-background text-foreground rounded-xl px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <Target className="w-4 h-4 inline mr-1" />
                  {t('mentalHealthGoals', { defaultValue: 'Mental Health Goals' })}
                </label>
                <textarea
                  value={formData.mental_health_goals || ''}
                  onChange={(e) => handleChange('mental_health_goals', e.target.value)}
                  placeholder={t('goalsPlaceholder', {
                    defaultValue: 'What are you hoping to achieve?',
                  })}
                  rows={3}
                  className="w-full border border-input bg-background text-foreground rounded-xl px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  <Users className="w-4 h-4 inline mr-1" />
                  {t('supportSystem', { defaultValue: 'Support System' })}
                </label>
                <textarea
                  value={formData.support_system || ''}
                  onChange={(e) => handleChange('support_system', e.target.value)}
                  placeholder={t('supportPlaceholder', {
                    defaultValue: 'Family, friends, community support...',
                  })}
                  rows={2}
                  className="w-full border border-input bg-background text-foreground rounded-xl px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('triggers', { defaultValue: 'Known Triggers' })}
                </label>
                <textarea
                  value={formData.triggers_notes || ''}
                  onChange={(e) => handleChange('triggers_notes', e.target.value)}
                  placeholder={t('triggersPlaceholder', {
                    defaultValue: 'Situations or things that may trigger distress...',
                  })}
                  rows={2}
                  className="w-full border border-input bg-background text-foreground rounded-xl px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  {t('copingStrategies', { defaultValue: 'Coping Strategies' })}
                </label>
                <textarea
                  value={formData.coping_strategies || ''}
                  onChange={(e) => handleChange('coping_strategies', e.target.value)}
                  placeholder={t('copingPlaceholder', {
                    defaultValue: 'What helps you cope when feeling stressed or anxious?',
                  })}
                  rows={2}
                  className="w-full border border-input bg-background text-foreground rounded-xl px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </DisclosurePanel>
          </Disclosure>

          {/* Save Button */}
          <Button type="submit" disabled={saving} className="w-full py-6 text-lg">
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                {t('saving', { defaultValue: 'Saving...' })}
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" />
                {t('saveProfile', { defaultValue: 'Save Profile' })}
              </>
            )}
          </Button>
        </form>

        {/* Data Export Link */}
        <Link
          href="/data-export"
          className="block bg-card border border-border rounded-xl p-4 hover:border-primary/50 transition-colors group"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-indigo-100 dark:bg-indigo-900/30 p-2 rounded-lg">
                <Download className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <p className="font-semibold text-foreground">{tDataExport('title')}</p>
                <p className="text-sm text-muted-foreground">{tDataExport('subtitle')}</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
        </Link>

        {/* Disconnect Confirmation Dialog */}
        <Dialog open={showDisconnectDialog} onClose={() => setShowDisconnectDialog(false)}>
          <DialogBackdrop />
          <DialogPanel>
            <DialogTitle>
              {t('myDoctor.disconnectTitle', { defaultValue: 'Disconnect from Doctor' })}
            </DialogTitle>
            <p className="text-muted-foreground mb-4">
              {t('myDoctor.disconnectWarning', {
                defaultValue:
                  'Are you sure you want to disconnect from your doctor? They will no longer be able to view your health data.',
              })}
            </p>
            {myDoctor && (
              <div className="bg-muted p-3 rounded-lg mb-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
                  {myDoctor.full_name[0]}
                </div>
                <div>
                  <p className="font-medium text-foreground">{myDoctor.full_name}</p>
                  {myDoctor.specialty && (
                    <p className="text-sm text-muted-foreground">{myDoctor.specialty}</p>
                  )}
                </div>
              </div>
            )}
            <div className="flex gap-3">
              <button
                onClick={() => setShowDisconnectDialog(false)}
                className="flex-1 px-4 py-2 border border-border text-muted-foreground rounded-lg hover:bg-muted transition-colors"
              >
                {common('cancel')}
              </button>
              <button
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="flex-1 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors disabled:opacity-50 flex items-center justify-center"
              >
                {disconnecting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  t('myDoctor.confirmDisconnect', { defaultValue: 'Disconnect' })
                )}
              </button>
            </div>
          </DialogPanel>
        </Dialog>

        {/* Doctor Profile Dialog */}
        <Dialog open={showDoctorProfileDialog} onClose={() => setShowDoctorProfileDialog(false)}>
          <DialogBackdrop />
          <DialogPanel className="max-w-lg">
            <div className="flex items-center justify-between mb-4">
              <DialogTitle className="mb-0">
                {t('myDoctor.profileTitle', { defaultValue: 'Doctor Profile' })}
              </DialogTitle>
              <button
                onClick={() => setShowDoctorProfileDialog(false)}
                className="p-1 hover:bg-muted rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-muted-foreground" />
              </button>
            </div>

            {loadingDoctorProfile ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              </div>
            ) : doctorProfile ? (
              <div className="space-y-4">
                {/* Doctor Header */}
                <div className="flex items-center gap-4 pb-4 border-b border-border">
                  <div className="w-16 h-16 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-2xl">
                    {doctorProfile.first_name[0]}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">
                      {doctorProfile.first_name} {doctorProfile.last_name}
                    </h3>
                    {doctorProfile.specialty && (
                      <p className="text-blue-600 dark:text-blue-400 font-medium">
                        {doctorProfile.specialty}
                      </p>
                    )}
                    {doctorProfile.years_of_experience && (
                      <p className="text-sm text-muted-foreground">
                        {doctorProfile.years_of_experience}{' '}
                        {t('myDoctor.yearsExp', { defaultValue: 'years experience' })}
                      </p>
                    )}
                  </div>
                </div>

                {/* Bio */}
                {doctorProfile.bio && (
                  <div>
                    <p className="text-sm text-muted-foreground">{doctorProfile.bio}</p>
                  </div>
                )}

                {/* Contact & Details */}
                <div className="space-y-3">
                  {doctorProfile.phone && (
                    <div className="flex items-center gap-3 text-sm">
                      <Phone className="w-4 h-4 text-muted-foreground" />
                      <span className="text-foreground">{doctorProfile.phone}</span>
                    </div>
                  )}

                  {doctorProfile.languages && (
                    <div className="flex items-center gap-3 text-sm">
                      <Languages className="w-4 h-4 text-muted-foreground" />
                      <span className="text-foreground">{doctorProfile.languages}</span>
                    </div>
                  )}

                  {doctorProfile.education && (
                    <div className="flex items-start gap-3 text-sm">
                      <GraduationCap className="w-4 h-4 text-muted-foreground mt-0.5" />
                      <span className="text-foreground">{doctorProfile.education}</span>
                    </div>
                  )}

                  {doctorProfile.consultation_hours && (
                    <div className="flex items-center gap-3 text-sm">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span className="text-foreground">{doctorProfile.consultation_hours}</span>
                    </div>
                  )}
                </div>

                {/* Clinic Info */}
                {(doctorProfile.clinic_name || doctorProfile.clinic_address) && (
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="flex items-start gap-3">
                      <Building className="w-4 h-4 text-muted-foreground mt-0.5" />
                      <div>
                        {doctorProfile.clinic_name && (
                          <p className="font-medium text-foreground">{doctorProfile.clinic_name}</p>
                        )}
                        {doctorProfile.clinic_address && (
                          <p className="text-sm text-muted-foreground">
                            {doctorProfile.clinic_address}
                          </p>
                        )}
                        {(doctorProfile.clinic_city || doctorProfile.clinic_country) && (
                          <p className="text-sm text-muted-foreground">
                            {[doctorProfile.clinic_city, doctorProfile.clinic_country]
                              .filter(Boolean)
                              .join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <button
                  onClick={() => setShowDoctorProfileDialog(false)}
                  className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                  {common('done')}
                </button>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                {t('myDoctor.noProfileData', { defaultValue: 'No profile information available' })}
              </div>
            )}
          </DialogPanel>
        </Dialog>
      </div>
    </div>
  )
}
