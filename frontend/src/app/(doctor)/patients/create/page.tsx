'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ArrowLeftIcon, Loader2Icon, UserPlusIcon, CopyIcon, CheckIcon, EyeIcon, EyeOffIcon } from '@/components/ui/icons';
import { cn } from '@/lib/utils';

interface FormData {
  email: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  preferred_language: string;
  emergency_contact: string;
  emergency_phone: string;
  emergency_contact_relationship: string;
  current_medications: string;
  medical_conditions: string;
  allergies: string;
  therapy_history: string;
  mental_health_goals: string;
  support_system: string;
  triggers_notes: string;
  coping_strategies: string;
}

interface CreatedPatient {
  patient_id: string;
  user_id: string;
  email: string;
  full_name: string;
  default_password: string;
  message: string;
}

export default function CreatePatientPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdPatient, setCreatedPatient] = useState<CreatedPatient | null>(null);
  const [copiedPassword, setCopiedPassword] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [activeSection, setActiveSection] = useState<'basic' | 'medical' | 'mental'>('basic');

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
  });

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.email.trim()) {
      setError('Email is required');
      return;
    }
    if (!formData.first_name.trim()) {
      setError('First name is required');
      return;
    }
    if (!formData.last_name.trim()) {
      setError('Last name is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Build request data, only including non-empty fields
      const requestData: Record<string, string> = {
        email: formData.email.trim(),
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
      };

      // Add optional fields if they have values
      Object.entries(formData).forEach(([key, value]) => {
        if (value && value.trim() && !['email', 'first_name', 'last_name'].includes(key)) {
          requestData[key] = value.trim();
        }
      });

      const result = await api.createPatient(requestData as unknown as Parameters<typeof api.createPatient>[0]);
      setCreatedPatient(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create patient');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPassword = async () => {
    if (createdPatient) {
      await navigator.clipboard.writeText(createdPatient.default_password);
      setCopiedPassword(true);
      setTimeout(() => setCopiedPassword(false), 2000);
    }
  };

  const handleCreateAnother = () => {
    setCreatedPatient(null);
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
    });
  };

  // Success state - show created patient info
  if (createdPatient) {
    return (
      <div className="max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="bg-card rounded-2xl shadow-sm border border-border p-8">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckIcon className="w-8 h-8 text-emerald-500" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">Patient Created Successfully</h2>
            <p className="text-muted-foreground mt-2">
              The patient account has been created and is ready to use.
            </p>
          </div>

          <div className="space-y-4 bg-muted/50 rounded-xl p-6 mb-6">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Patient Name</span>
              <span className="font-medium text-foreground">{createdPatient.full_name}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Email</span>
              <span className="font-medium text-foreground">{createdPatient.email}</span>
            </div>
            <div className="border-t border-border pt-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Default Password</span>
                <div className="flex items-center gap-2">
                  <code className={cn(
                    "px-3 py-1 bg-background rounded border border-border font-mono text-sm",
                    !showPassword && "tracking-widest"
                  )}>
                    {showPassword ? createdPatient.default_password : '••••••••••'}
                  </code>
                  <button
                    onClick={() => setShowPassword(!showPassword)}
                    className="p-1.5 hover:bg-muted rounded-lg transition-colors"
                    title={showPassword ? 'Hide password' : 'Show password'}
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
                    title="Copy password"
                  >
                    {copiedPassword ? (
                      <CheckIcon className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <CopyIcon className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>
                </div>
              </div>
              <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                Please share this password with the patient. They will be required to change it on first login.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleCreateAnother}
              className="flex-1 px-4 py-2.5 border border-border text-foreground rounded-xl hover:bg-muted transition-colors"
            >
              Create Another
            </button>
            <Link
              href={`/patients/${createdPatient.patient_id}`}
              className="flex-1 px-4 py-2.5 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors text-center"
            >
              View Patient
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href="/patients"
          className="p-2 hover:bg-muted rounded-lg transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5 text-muted-foreground" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Create New Patient</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Create a patient account and automatically connect them to you
          </p>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="bg-card rounded-xl border border-border p-1 mb-6 flex gap-1">
        <button
          onClick={() => setActiveSection('basic')}
          className={cn(
            "flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            activeSection === 'basic'
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted"
          )}
        >
          Basic Information
        </button>
        <button
          onClick={() => setActiveSection('medical')}
          className={cn(
            "flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            activeSection === 'medical'
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted"
          )}
        >
          Medical History
        </button>
        <button
          onClick={() => setActiveSection('mental')}
          className={cn(
            "flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            activeSection === 'mental'
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted"
          )}
        >
          Mental Health
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
                    Email <span className="text-red-500">*</span>
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
                      First Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.first_name}
                      onChange={(e) => handleInputChange('first_name', e.target.value)}
                      placeholder="First name"
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Last Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.last_name}
                      onChange={(e) => handleInputChange('last_name', e.target.value)}
                      placeholder="Last name"
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                      required
                    />
                  </div>
                </div>

                {/* Optional fields */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Date of Birth
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
                    Gender
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                    <option value="prefer_not_to_say">Prefer not to say</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Phone
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
                    Preferred Language
                  </label>
                  <select
                    value={formData.preferred_language}
                    onChange={(e) => handleInputChange('preferred_language', e.target.value)}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  >
                    <option value="">Select language</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="ar">Arabic</option>
                    <option value="bn">Bengali</option>
                    <option value="fa">Persian</option>
                    <option value="zh">Chinese</option>
                  </select>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Address
                  </label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    placeholder="Street address"
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => handleInputChange('city', e.target.value)}
                    placeholder="City"
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) => handleInputChange('country', e.target.value)}
                    placeholder="Country"
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>
              </div>

              {/* Emergency Contact */}
              <div className="border-t border-border pt-6">
                <h3 className="text-lg font-semibold text-foreground mb-4">Emergency Contact</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Contact Name
                    </label>
                    <input
                      type="text"
                      value={formData.emergency_contact}
                      onChange={(e) => handleInputChange('emergency_contact', e.target.value)}
                      placeholder="Emergency contact name"
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.emergency_phone}
                      onChange={(e) => handleInputChange('emergency_phone', e.target.value)}
                      placeholder="Emergency contact phone"
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Relationship
                    </label>
                    <input
                      type="text"
                      value={formData.emergency_contact_relationship}
                      onChange={(e) => handleInputChange('emergency_contact_relationship', e.target.value)}
                      placeholder="e.g., Spouse, Parent"
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
                  Current Medications
                </label>
                <textarea
                  value={formData.current_medications}
                  onChange={(e) => handleInputChange('current_medications', e.target.value)}
                  placeholder="List current medications and dosages..."
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Medical Conditions
                </label>
                <textarea
                  value={formData.medical_conditions}
                  onChange={(e) => handleInputChange('medical_conditions', e.target.value)}
                  placeholder="List any existing medical conditions..."
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Allergies
                </label>
                <textarea
                  value={formData.allergies}
                  onChange={(e) => handleInputChange('allergies', e.target.value)}
                  placeholder="List any known allergies..."
                  rows={2}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Therapy History
                </label>
                <textarea
                  value={formData.therapy_history}
                  onChange={(e) => handleInputChange('therapy_history', e.target.value)}
                  placeholder="Previous therapy or counseling experience..."
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
                  Mental Health Goals
                </label>
                <textarea
                  value={formData.mental_health_goals}
                  onChange={(e) => handleInputChange('mental_health_goals', e.target.value)}
                  placeholder="What does the patient hope to achieve through therapy?"
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Support System
                </label>
                <textarea
                  value={formData.support_system}
                  onChange={(e) => handleInputChange('support_system', e.target.value)}
                  placeholder="Family, friends, community support available..."
                  rows={2}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Known Triggers
                </label>
                <textarea
                  value={formData.triggers_notes}
                  onChange={(e) => handleInputChange('triggers_notes', e.target.value)}
                  placeholder="Situations or events that may trigger distress..."
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Coping Strategies
                </label>
                <textarea
                  value={formData.coping_strategies}
                  onChange={(e) => handleInputChange('coping_strategies', e.target.value)}
                  placeholder="Current coping mechanisms and strategies..."
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
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-2.5 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2Icon className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <UserPlusIcon className="w-4 h-4" />
                  Create Patient
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
