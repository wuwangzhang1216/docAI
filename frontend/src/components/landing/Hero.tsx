'use client';

import Link from 'next/link';
import { ArrowRight, ShieldCheck, Activity, MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

export function Hero() {
    return (
        <div className="relative overflow-hidden bg-background pt-[120px] pb-16 md:pt-[150px] md:pb-32">
            <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="text-center">
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl"
                    >
                        Your Personal
                        <span className="text-primary block mt-2">AI Mental Health Companion</span>
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.1 }}
                        className="mt-6 text-lg leading-8 text-muted-foreground max-w-2xl mx-auto"
                    >
                        Heart Guardian AI provides 24/7 emotional support, mood tracking, and professional connection.
                        A safe space for your mental well-being, available whenever you need it.
                    </motion.p>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                        className="mt-10 flex items-center justify-center gap-x-6"
                    >
                        <Link href="/login">
                            <Button size="lg" className="h-12 px-8 text-lg rounded-full">
                                Get Started <ArrowRight className="ml-2 h-5 w-5" />
                            </Button>
                        </Link>
                        <Link href="#features">
                            <Button variant="ghost" size="lg" className="h-12 px-8 text-lg rounded-full">
                                Learn more <span aria-hidden="true" className="ml-2">→</span>
                            </Button>
                        </Link>
                    </motion.div>
                </div>

                {/* Floating Icons illustration */}
                <div className="mt-16 sm:mt-24 relative">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8, delay: 0.3 }}
                        className="mx-auto max-w-5xl rounded-3xl p-4 bg-muted/30 border border-border/50 backdrop-blur-sm"
                    >
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 p-8 items-center justify-items-center">
                            <div className="flex flex-col items-center gap-4 p-6 rounded-2xl bg-card border shadow-sm w-full max-w-xs">
                                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                                    <MessageCircle className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                                </div>
                                <h3 className="font-semibold">24/7 AI Chat</h3>
                                <p className="text-center text-sm text-muted-foreground">Always there to listen and support you.</p>
                            </div>
                            <div className="flex flex-col items-center gap-4 p-6 rounded-2xl bg-card border shadow-sm w-full max-w-xs transform md:-translate-y-8">
                                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-full">
                                    <ShieldCheck className="w-8 h-8 text-green-600 dark:text-green-400" />
                                </div>
                                <h3 className="font-semibold">Private & Secure</h3>
                                <p className="text-center text-sm text-muted-foreground">Your data is encrypted and protected.</p>
                            </div>
                            <div className="flex flex-col items-center gap-4 p-6 rounded-2xl bg-card border shadow-sm w-full max-w-xs">
                                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full">
                                    <Activity className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                                </div>
                                <h3 className="font-semibold">Mood Tracking</h3>
                                <p className="text-center text-sm text-muted-foreground">Monitor your emotional journey over time.</p>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
