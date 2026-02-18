'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useAuth, getRedirectPath } from '@/lib/auth';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeSwitcher';
import {
  User,
  Stethoscope,
  Mail,
  Lock,
  UserCircle2,
  Loader2,
  ArrowRight,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';

type Mode = 'login' | 'register';
type UserType = 'PATIENT' | 'DOCTOR';

export default function LoginPage() {
  const router = useRouter();
  const { login, register, sessionExpired, clearSessionExpired } = useAuth();
  const t = useTranslations('login');
  const common = useTranslations('common');

  // Clear session expired flag when user navigates away or logs in successfully
  useEffect(() => {
    return () => {
      if (sessionExpired) {
        clearSessionExpired();
      }
    };
  }, [sessionExpired, clearSessionExpired]);

  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [userType, setUserType] = useState<UserType>('PATIENT');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'login') {
        const result = await login(email, password);

        // Check if password must be changed (for doctor-created accounts)
        if (result.passwordMustChange) {
          router.push('/change-password');
          return;
        }
      } else {
        await register(email, password, userType, firstName, lastName);
      }

      // Get user type from localStorage after login/register
      const storedUserType = localStorage.getItem('user_type') as UserType;
      router.push(getRedirectPath(storedUserType));
    } catch (err) {
      setError(err instanceof Error ? err.message : common('error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-muted/50 dark:from-background dark:via-background dark:to-muted/20 relative overflow-hidden p-4">
      {/* Language Switcher & Theme Toggle */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
        <ThemeToggle className="bg-card/80 backdrop-blur-sm shadow-sm rounded-lg border border-border/50" />
        <LanguageSwitcher className="bg-card/80 backdrop-blur-sm shadow-sm rounded-lg px-3 py-1.5 border border-border/50" />
      </div>

      <div className="max-w-[400px] w-full relative z-10">
        {/* Logo and Title */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary shadow-lg shadow-primary/30 mb-4">
            <UserCircle2 className="w-6 h-6 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('title')}</h1>
          <p className="text-muted-foreground text-sm mt-2">{t('subtitle')}</p>
        </div>

        {/* Form Card */}
        <Card className="border-border/50 shadow-apple-xl bg-card dark:bg-card/95 dark:border-white/[0.06]">
          <CardContent className="p-6">
            {/* Mode Toggle */}
            <div className="grid grid-cols-2 gap-1 bg-muted/50 dark:bg-muted p-1 rounded-lg mb-6">
              <Button
                variant={mode === 'login' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setMode('login')}
                className={cn(
                  "w-full shadow-none",
                  mode === 'login'
                    ? "bg-background dark:bg-background text-foreground hover:bg-background hover:text-foreground shadow-sm"
                    : "hover:bg-transparent text-muted-foreground"
                )}
              >
                {t('loginTab')}
              </Button>
              <Button
                variant={mode === 'register' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setMode('register')}
                className={cn(
                  "w-full shadow-none",
                  mode === 'register'
                    ? "bg-background dark:bg-background text-foreground hover:bg-background hover:text-foreground shadow-sm"
                    : "hover:bg-transparent text-muted-foreground"
                )}
              >
                {t('registerTab')}
              </Button>
            </div>

            {/* Session Expired Message */}
            {sessionExpired && (
              <div className="mb-6 p-3 bg-amber-500/10 text-amber-700 dark:text-amber-400 text-sm rounded-md flex items-center font-medium border border-amber-500/20">
                <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                {t('sessionExpired', { defaultValue: 'Your session has expired. Please log in again.' })}
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-3 bg-destructive/10 text-destructive text-sm rounded-md flex items-center font-medium">
                <div className="w-1.5 h-1.5 rounded-full bg-destructive mr-2" />
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* First Name and Last Name (Register only) */}
              {mode === 'register' && (
                <div className="grid grid-cols-2 gap-3 animate-in fade-in slide-in-from-top-2">
                  <div className="space-y-2">
                    <label className="text-xs font-semibold uppercase tracking-wide text-foreground/70">
                      {t('firstNameLabel')}
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        required
                        placeholder={t('firstNamePlaceholder')}
                        className="pl-9 bg-muted/50 dark:bg-muted border-border"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-semibold uppercase tracking-wide text-foreground/70">
                      {t('lastNameLabel')}
                    </label>
                    <Input
                      type="text"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      required
                      placeholder={t('lastNamePlaceholder')}
                      className="bg-muted/50 dark:bg-muted border-border"
                    />
                  </div>
                </div>
              )}

              {/* Email */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-foreground/70">
                  {t('emailLabel')}
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="name@example.com"
                    className="pl-9 bg-muted/50 dark:bg-muted border-border"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-foreground/70">
                  {t('passwordLabel')}
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    placeholder="••••••••"
                    className="pl-9 bg-muted/50 dark:bg-muted border-border"
                  />
                </div>
              </div>

              {/* User Type (Register only) */}
              {mode === 'register' && (
                <div className="space-y-2 pt-2 animate-in fade-in slide-in-from-top-2">
                  <label className="text-xs font-semibold uppercase tracking-wide text-foreground/70">
                    {t('selectIdentity')}
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <button
                      type="button"
                      onClick={() => setUserType('PATIENT')}
                      className={cn(
                        "flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all",
                        userType === 'PATIENT'
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-muted/30 dark:bg-muted/50 text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                      )}
                    >
                      <User className="w-5 h-5 mb-2" />
                      <span className="font-medium text-xs">{t('patient')}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setUserType('DOCTOR')}
                      className={cn(
                        "flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all",
                        userType === 'DOCTOR'
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-muted/30 dark:bg-muted/50 text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                      )}
                    >
                      <Stethoscope className="w-5 h-5 mb-2" />
                      <span className="font-medium text-xs">{t('doctor')}</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full mt-4"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {t('processing')}
                  </>
                ) : (
                  <>
                    {mode === 'login' ? t('loginButton') : t('registerButton')}
                    <ArrowRight className="w-4 h-4 ml-2 opacity-80" />
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <p className="text-center text-xs text-muted-foreground mt-8 leading-relaxed px-4">
          {t('disclaimer1')}
          <br />
          {t('disclaimer2')}
        </p>
      </div>
    </div>
  );
}
