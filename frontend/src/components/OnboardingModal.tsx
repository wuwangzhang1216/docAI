'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Dialog, DialogBackdrop, DialogPanel } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  MessageCircle,
  Heart,
  Users,
  User,
  ChevronRight,
  ChevronLeft,
  X,
  Sparkles,
} from 'lucide-react';

const ONBOARDING_KEY = 'xinshou_onboarding_completed';

interface OnboardingModalProps {
  forceShow?: boolean;
}

export function OnboardingModal({ forceShow = false }: OnboardingModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const t = useTranslations('patient.onboarding');

  useEffect(() => {
    // Check if user has already completed onboarding
    if (forceShow) {
      setIsOpen(true);
      return;
    }

    const hasCompleted = localStorage.getItem(ONBOARDING_KEY);
    if (!hasCompleted) {
      // Small delay to ensure smooth transition after login
      const timer = setTimeout(() => {
        setIsOpen(true);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [forceShow]);

  const handleComplete = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setIsOpen(false);
  };

  const handleSkip = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setIsOpen(false);
  };

  const steps = [
    {
      icon: Sparkles,
      iconBg: 'bg-primary/10',
      iconColor: 'text-primary',
      title: t('step1.title', { defaultValue: 'Welcome to Heart Guardian' }),
      description: t('step1.description', { defaultValue: 'Your safe space for mental health support. We\'re here to help you on your journey to well-being.' }),
    },
    {
      icon: MessageCircle,
      iconBg: 'bg-blue-500/10',
      iconColor: 'text-blue-600 dark:text-blue-400',
      title: t('step2.title', { defaultValue: 'Talk to AI Anytime' }),
      description: t('step2.description', { defaultValue: 'Chat with our AI companion for emotional support, 24/7. It\'s a safe space to share your thoughts and feelings.' }),
    },
    {
      icon: Heart,
      iconBg: 'bg-purple-500/10',
      iconColor: 'text-purple-600 dark:text-purple-400',
      title: t('step3.title', { defaultValue: 'Track Your Health' }),
      description: t('step3.description', { defaultValue: 'Log daily check-ins and take assessments to understand your mental health better. Your data helps you and your doctor.' }),
    },
    {
      icon: Users,
      iconBg: 'bg-green-500/10',
      iconColor: 'text-green-600 dark:text-green-400',
      title: t('step4.title', { defaultValue: 'Connect with Your Doctor' }),
      description: t('step4.description', { defaultValue: 'When your doctor sends a connection request, you can share your health data securely for better care.' }),
    },
    {
      icon: User,
      iconBg: 'bg-orange-500/10',
      iconColor: 'text-orange-600 dark:text-orange-400',
      title: t('step5.title', { defaultValue: 'Complete Your Profile' }),
      description: t('step5.description', { defaultValue: 'Take a moment to fill in your profile. This helps us personalize your experience and helps your healthcare provider.' }),
    },
  ];

  const currentStepData = steps[currentStep];
  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  return (
    <Dialog open={isOpen} onClose={() => {}}>
      <DialogBackdrop />
      <DialogPanel className="max-w-md">
        {/* Skip button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 p-1 text-muted-foreground hover:text-foreground transition-colors"
          aria-label={t('skip', { defaultValue: 'Skip' })}
        >
          <X className="w-5 h-5" />
        </button>

        {/* Content */}
        <div className="pt-6 pb-4 text-center">
          {/* Icon */}
          <div className={`w-16 h-16 mx-auto rounded-2xl ${currentStepData.iconBg} flex items-center justify-center mb-4`}>
            <currentStepData.icon className={`w-8 h-8 ${currentStepData.iconColor}`} />
          </div>

          {/* Title */}
          <h2 className="text-xl font-bold text-foreground mb-2">
            {currentStepData.title}
          </h2>

          {/* Description */}
          <p className="text-muted-foreground text-sm leading-relaxed px-4">
            {currentStepData.description}
          </p>
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-1.5 py-4">
          {steps.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentStep(index)}
              className={`w-2 h-2 rounded-full transition-all ${
                index === currentStep
                  ? 'bg-primary w-6'
                  : 'bg-muted-foreground/30 hover:bg-muted-foreground/50'
              }`}
              aria-label={`Go to step ${index + 1}`}
            />
          ))}
        </div>

        {/* Navigation buttons */}
        <div className="flex gap-3 pt-2">
          {!isFirstStep && (
            <Button
              variant="outline"
              onClick={() => setCurrentStep((prev) => prev - 1)}
              className="flex-1"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              {t('back', { defaultValue: 'Back' })}
            </Button>
          )}

          {isLastStep ? (
            <Button
              onClick={handleComplete}
              className="flex-1"
            >
              {t('getStarted', { defaultValue: 'Get Started' })}
            </Button>
          ) : (
            <Button
              onClick={() => setCurrentStep((prev) => prev + 1)}
              className="flex-1"
            >
              {t('next', { defaultValue: 'Next' })}
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          )}
        </div>
      </DialogPanel>
    </Dialog>
  );
}

// Hook to check if onboarding has been completed
export function useOnboardingStatus() {
  const [hasCompleted, setHasCompleted] = useState(true);

  useEffect(() => {
    const completed = localStorage.getItem(ONBOARDING_KEY);
    setHasCompleted(!!completed);
  }, []);

  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_KEY);
    setHasCompleted(false);
  };

  return { hasCompleted, resetOnboarding };
}
