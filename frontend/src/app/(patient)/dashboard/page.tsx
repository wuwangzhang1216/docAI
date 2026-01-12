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
        <div className="px-6 py-8 space-y-8 pb-24">
            {/* Greeting Section */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-3"
            >
                <div className="p-3 bg-primary/10 rounded-full">
                    <Icon className="w-6 h-6 text-primary" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">{greeting}</h1>
                    <p className="text-muted-foreground text-sm">How are you feeling today?</p>
                </div>
            </motion.div>

            {/* Mood Quick Select (Mock) */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
            >
                <Card className="border-border/50 shadow-sm">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-base font-medium">Quick Mood Check</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex justify-between gap-2">
                            {['😢', '😕', '😐', '🙂', '😄'].map((emoji, i) => (
                                <button
                                    key={i}
                                    className="text-2xl p-3 hover:bg-muted rounded-xl transition-colors w-full flex items-center justify-center bg-muted/20"
                                >
                                    {emoji}
                                </button>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Main Actions Grid */}
            <div className="grid gap-4">
                {actions.map((action, i) => (
                    <motion.div
                        key={action.title}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 + (i * 0.1) }}
                    >
                        <Link href={action.href}>
                            <Card className="hover:bg-muted/30 transition-colors border-border/50 shadow-sm cursor-pointer group">
                                <CardContent className="p-4 flex items-center gap-4">
                                    <div className={`p-3 rounded-xl ${action.bg}`}>
                                        <action.icon className={`w-6 h-6 ${action.color}`} />
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-semibold">{action.title}</h3>
                                        <p className="text-xs text-muted-foreground">{action.desc}</p>
                                    </div>
                                    <ArrowRight className="w-5 h-5 text-muted-foreground opacity-20 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                                </CardContent>
                            </Card>
                        </Link>
                    </motion.div>
                ))}
            </div>

            {/* Quote of the day placeholder */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="text-center p-6 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/10"
            >
                <p className="italic text-sm text-foreground/80">
                    "The only journey is the one within."
                </p>
                <p className="text-xs text-muted-foreground mt-2">— Rainer Maria Rilke</p>
            </motion.div>
        </div>
    );
}
