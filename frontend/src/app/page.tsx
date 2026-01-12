'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth, getRedirectPath } from '@/lib/auth';
import { Header } from '@/components/landing/Header';
import { Hero } from '@/components/landing/Hero';
import { Footer } from '@/components/landing/Footer';
import { Loader2 } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, userType, isLoading } = useAuth();
  const [showLanding, setShowLanding] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated && userType) {
        // user is logged in, redirect to their dashboard
        // Note: We'll need to update getRedirectPath to point to /dashboard for patients later
        router.push(getRedirectPath(userType));
      } else {
        // User is not logged in, show landing page
        setShowLanding(true);
      }
    }
  }, [isAuthenticated, userType, isLoading, router]);

  // While checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 text-primary animate-spin" />
      </div>
    );
  }

  // If authenticated, we are redirecting, so return null or loader
  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center">
          <Loader2 className="h-8 w-8 text-primary animate-spin mb-4" />
          <p className="text-muted-foreground">Welcome back, redirecting...</p>
        </div>
      </div>
    );
  }

  // Show Landing Page
  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary/10">
      <Header />
      <main className="flex-1">
        <Hero />
      </main>
      <Footer />
    </div>
  );
}
