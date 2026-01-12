'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/lib/auth';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeSwitcher';
import { MessageCircle, Heart, UserCircle2, User, Calendar, Home } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { OnboardingModal } from '@/components/OnboardingModal';

export default function PatientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, userType, isLoading, logout } = useAuth();
  const t = useTranslations('patient.nav');
  const common = useTranslations('common');

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/login');
      } else if (userType !== 'PATIENT') {
        router.push('/patients');
      }
    }
  }, [isAuthenticated, userType, isLoading, router]);

  if (isLoading || !isAuthenticated || userType !== 'PATIENT') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mb-4"></div>
          <p className="text-muted-foreground text-sm">{common('loading')}</p>
        </div>
      </div>
    );
  }

  const navItems = [
    { href: '/dashboard', label: t('home', { defaultValue: 'Home' }), icon: Home },
    { href: '/conversations', label: t('conversations', { defaultValue: 'Chat' }), icon: MessageCircle },
    { href: '/my-appointments', label: t('appointments', { defaultValue: 'Appointments' }), icon: Calendar },
    { href: '/health', label: t('health', { defaultValue: 'Health' }), icon: Heart },
    { href: '/profile', label: t('profile', { defaultValue: 'Profile' }), icon: User },
  ];

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <div className="h-[100dvh] flex flex-col bg-background overflow-hidden">
      {/* Header */}
      <header className="absolute top-0 w-full bg-background/80 backdrop-blur-md border-b border-border z-50">
        <div className="max-w-lg mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="bg-primary/10 p-2 rounded-xl">
              <UserCircle2 className="w-5 h-5 text-primary" />
            </div>
            <h1 className="text-lg font-bold text-foreground tracking-tight">{common('appName')}</h1>
          </div>
          <div className="flex items-center space-x-1">
            <ThemeToggle />
            <LanguageSwitcher />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 h-8 px-3"
            >
              {common('logout')}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative w-full max-w-lg mx-auto animate-in fade-in duration-500 bg-muted/20 pt-[60px]">
        {children}
        <OnboardingModal />
      </main>

      {/* Bottom Navigation */}
      <nav className="flex-none bg-background/90 backdrop-blur-md border-t border-border z-50">
        <div className="max-w-lg mx-auto px-6">
          <div className="flex justify-between items-center py-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex flex-col items-center py-2 px-3 rounded-2xl transition-all duration-300",
                    isActive
                      ? "text-primary bg-primary/10 transform scale-105"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                >
                  <Icon className={cn("w-6 h-6 mb-1", isActive && "fill-current opacity-20")} strokeWidth={isActive ? 2.5 : 2} />
                  <span className={cn("text-[10px] font-medium", isActive ? "text-primary" : "text-muted-foreground")}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </nav>
    </div>
  );
}
