'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeSwitcher';
import {
  UsersIcon,
  AlertTriangleIcon,
  LogOutIcon,
  StethoscopeIcon,
  UserIcon,
  MailIcon,
  CalendarIcon,
} from '@/components/ui/icons';
import { cn } from '@/lib/utils';

export default function DoctorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, userType, isLoading, logout } = useAuth();
  const [pendingRequestsCount, setPendingRequestsCount] = useState(0);
  const t = useTranslations('doctor.nav');
  const common = useTranslations('common');
  const doctor = useTranslations('doctor');

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/login');
      } else if (userType !== 'DOCTOR') {
        router.push('/chat');
      }
    }
  }, [isAuthenticated, userType, isLoading, router]);

  // Fetch pending connection requests count
  useEffect(() => {
    const fetchPendingRequests = async () => {
      if (!isAuthenticated || userType !== 'DOCTOR') return;
      try {
        const response = await api.getConnectionRequests({ status: 'PENDING', limit: 100 });
        setPendingRequestsCount(response.total || response.items?.length || 0);
      } catch {
        console.error('Failed to fetch pending requests');
      }
    };
    fetchPendingRequests();
    // Refresh every 30 seconds
    const interval = setInterval(fetchPendingRequests, 30000);
    return () => clearInterval(interval);
  }, [isAuthenticated, userType]);

  if (isLoading || !isAuthenticated || userType !== 'DOCTOR') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mb-4"></div>
          <p className="text-muted-foreground text-sm">{doctor('loadingWorkspace')}</p>
        </div>
      </div>
    );
  }

  const navItems = [
    { href: '/patients', label: t('patients'), icon: UsersIcon },
    { href: '/appointments', label: t('appointments', { defaultValue: '预约管理' }), icon: CalendarIcon },
    { href: '/doctor-messages', label: t('messages', { defaultValue: 'Messages' }), icon: MailIcon },
    { href: '/risk-queue', label: t('riskQueue'), icon: AlertTriangleIcon },
    { href: '/my-profile', label: t('profile'), icon: UserIcon },
  ];

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="bg-background/80 backdrop-blur-md border-b border-border sticky top-0 z-50 transition-all duration-200">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="bg-primary p-1.5 rounded-lg shadow-sm">
                <StethoscopeIcon className="w-5 h-5 text-primary-foreground" />
              </div>
              <h1 className="text-lg font-bold text-foreground tracking-tight">{common('appName')} <span className="text-muted-foreground font-normal ml-1 text-sm bg-muted px-2 py-0.5 rounded-full">{common('doctorBadge')}</span></h1>
            </div>

            <div className="flex items-center space-x-1">
              <ThemeToggle />
              <LanguageSwitcher />
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 px-3 py-1.5 text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors duration-200"
              >
                <LogOutIcon className="w-4 h-4" />
                <span>{common('logout')}</span>
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 -mb-px overflow-x-auto no-scrollbar">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname.startsWith(item.href);
              const showBadge = item.href === '/patients' && pendingRequestsCount > 0;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "relative flex items-center space-x-2 py-3 px-4 border-b-2 font-medium text-sm transition-all duration-200 whitespace-nowrap",
                    isActive
                      ? "border-primary text-primary bg-primary/10"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                  )}
                >
                  <Icon className={cn("w-4 h-4", isActive ? "stroke-[2.5px]" : "stroke-2")} />
                  <span>{item.label}</span>
                  {showBadge && (
                    <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-destructive text-destructive-foreground text-[10px] font-bold rounded-full px-1">
                      {pendingRequestsCount > 99 ? '99+' : pendingRequestsCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-6xl mx-auto p-4 md:p-6 animate-in fade-in duration-500">
        {children}
      </main>
    </div>
  );
}
