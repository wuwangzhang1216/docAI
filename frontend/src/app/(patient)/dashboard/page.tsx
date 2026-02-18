'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
    MessageCircle,
    Calendar,
    Heart,
    Sun,
    Moon,
    CloudSun,
    ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const springTransition = { type: "spring" as const, stiffness: 200, damping: 25 };

export default function DashboardPage() {
    const t = useTranslations('patient.nav'); // Reusing nav translations for now or generic
    // In a real app we would check time of day
    const hour = new Date().getHours();
    let greeting = 'Good Morning';
    let Icon = Sun;

    if (hour >= 12 && hour < 17) {
        greeting = 'Good Afternoon';
        Icon = CloudSun;
    } else if (hour >= 17) {
        greeting = 'Good Evening';
        Icon = Moon;
    }

    // Quick actions config
    const actions = [
        {
            title: 'Talk to AI',
            desc: 'Get immediate emotional support',
            icon: MessageCircle,
            href: '/conversations',
            color: 'text-blue-500',
            bg: 'bg-blue-500/10'
        },
        {
            title: 'Health Center',
            desc: 'Check-ins & assessments',
            icon: Heart,
            href: '/health',
            color: 'text-purple-500',
            bg: 'bg-purple-500/10'
        },
        {
            title: 'Appointments',
            desc: 'View upcoming sessions',
            icon: Calendar,
            href: '/my-appointments',
            color: 'text-green-500',
            bg: 'bg-green-500/10'
        }
    ];

    return (
        <div className="px-6 py-10 md:px-8 md:py-8 pb-24 md:pb-8 max-w-4xl md:mx-auto">
            {/* Greeting Section */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={springTransition}
                className="flex items-center gap-4"
            >
                <div className="p-3 bg-primary/10 rounded-full">
                    <Icon className="w-6 h-6 text-primary" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">{greeting}</h1>
                    <p className="text-muted-foreground text-sm">How are you feeling today?</p>
                </div>
            </motion.div>

            {/* Responsive Grid: single column on mobile, two columns on desktop */}
            <div className="mt-8 grid md:grid-cols-[1fr_320px] gap-6 md:gap-8">
                {/* Left Column: Action Cards */}
                <div className="space-y-4 order-2 md:order-1">
                    {actions.map((action, i) => (
                        <motion.div
                            key={action.title}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ ...springTransition, delay: 0.2 + (i * 0.08) }}
                        >
                            <Link href={action.href}>
                                <Card className="transition-all duration-300 border-border/50 shadow-apple-sm cursor-pointer group hover:shadow-apple-md hover:-translate-y-0.5">
                                    <CardContent className="p-4 flex items-center gap-4">
                                        <div className={`p-3 rounded-xl ${action.bg}`}>
                                            <action.icon className={`w-6 h-6 ${action.color}`} />
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="font-semibold">{action.title}</h3>
                                            <p className="text-xs text-muted-foreground">{action.desc}</p>
                                        </div>
                                        <ArrowRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
                                    </CardContent>
                                </Card>
                            </Link>
                        </motion.div>
                    ))}
                </div>

                {/* Right Column: Mood + Quote */}
                <div className="space-y-6 order-1 md:order-2">
                    {/* Mood Quick Select */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ ...springTransition, delay: 0.1 }}
                    >
                        <Card className="border-border/50 shadow-apple-sm">
                            <CardHeader className="pb-3">
                                <CardTitle className="text-base font-medium">Quick Mood Check</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="flex justify-between gap-2">
                                    {['😢', '😕', '😐', '🙂', '😄'].map((emoji, i) => (
                                        <button
                                            key={i}
                                            className="text-2xl p-3 hover:bg-muted rounded-xl transition-all duration-200 w-full flex items-center justify-center bg-muted/20 hover:scale-105 active:scale-95"
                                        >
                                            {emoji}
                                        </button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Quote of the day */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ ...springTransition, delay: 0.5 }}
                        className="text-center p-8 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/10"
                    >
                        <p className="italic text-sm text-foreground/80 leading-relaxed">
                            &ldquo;The only journey is the one within.&rdquo;
                        </p>
                        <p className="text-xs text-muted-foreground mt-3">— Rainer Maria Rilke</p>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
