'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { UserCircle2 } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeSwitcher';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

export function Header() {
    return (
        <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-primary/10 p-2 rounded-xl">
                            <UserCircle2 className="w-6 h-6 text-primary" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">HeartGuard</span>
                    </div>

                    <nav className="hidden md:flex gap-8">
                        <Link href="#features" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                            Features
                        </Link>
                        <Link href="#about" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                            About
                        </Link>
                    </nav>

                    <div className="flex items-center gap-4">
                        <div className="hidden sm:flex gap-2">
                            <ThemeToggle />
                            <LanguageSwitcher />
                        </div>
                        <Link href="/login">
                            <Button>Sign In</Button>
                        </Link>
                    </div>
                </div>
            </div>
        </header>
    );
}
