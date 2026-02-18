'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/lib/auth';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeSwitcher';
import { MessageCircle, Heart, UserCircle2, User, Calendar, Home, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { OnboardingModal } from '@/components/OnboardingModal';
import { motion } from 'framer-motion';

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
    <div className="h-[100dvh] flex flex-col md:flex-row bg-background overflow-hidden">
      {/* ===== Desktop Sidebar ===== */}
      <aside className="hidden md:flex flex-col w-[260px] shrink-0 h-full bg-background/70 backdrop-blur-xl backdrop-saturate-150 border-r border-border/40 z-50">
        {/* App Logo */}
        <div className="px-5 py-5 flex items-center space-x-3">
          <div className="bg-primary/10 p-2 rounded-xl">
            <UserCircle2 className="w-5 h-5 text-primary" />
          </div>
          <h1 className="text-lg font-bold text-foreground tracking-tight">{common('appName')}</h1>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 py-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative flex items-center gap-3 px-4 py-2.5 mx-3 rounded-xl transition-colors duration-200",
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTabDesktop"
                    className="absolute inset-0 bg-primary/10 rounded-xl"
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon className="w-5 h-5 relative z-10" strokeWidth={isActive ? 2.5 : 1.8} />
                <span className={cn(
                  "text-sm font-medium relative z-10",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom: Theme, Language, Logout */}
        <div className="p-4 border-t border-border/40 space-y-3">
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <LanguageSwitcher />
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 h-9"
          >
            <LogOut className="w-4 h-4" />
            {common('logout')}
          </Button>
        </div>
      </aside>

      {/* ===== Main Area ===== */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header */}
        <header className="md:hidden absolute top-0 w-full bg-background/70 backdrop-blur-xl backdrop-saturate-150 border-b border-border/40 z-50">
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
        <main className="flex-1 overflow-y-auto relative w-full max-w-lg md:max-w-none mx-auto animate-in fade-in duration-500 bg-muted/20 pt-[60px] md:pt-0">
          {children}
          <OnboardingModal />
        </main>

        {/* Mobile Bottom Navigation */}
        <nav className="md:hidden flex-none bg-background/70 backdrop-blur-xl backdrop-saturate-150 border-t border-border/40 z-50">
          <div className="max-w-lg mx-auto px-4">
            <div className="flex justify-between items-center py-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "relative flex flex-col items-center min-h-[44px] min-w-[44px] py-2 px-3 rounded-2xl transition-colors duration-200",
                      isActive
                        ? "text-primary"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="activeTabMobile"
                        className="absolute inset-0 bg-primary/10 rounded-2xl"
                        transition={{ type: "spring", stiffness: 350, damping: 30 }}
                      />
                    )}
                    <Icon
                      className={cn("w-6 h-6 mb-1 relative z-10")}
                      strokeWidth={isActive ? 2.5 : 1.8}
                    />
                    <span className={cn(
                      "text-[11px] font-medium relative z-10",
                      isActive ? "text-primary" : "text-muted-foreground"
                    )}>
                      {item.label}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        </nav>
      </div>
    </div>
  );
}
