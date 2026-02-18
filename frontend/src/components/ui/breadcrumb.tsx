import * as React from 'react'
import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

function Breadcrumb({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center text-sm', className)}>
      <ol className="flex items-center gap-1.5">{children}</ol>
    </nav>
  )
}

function BreadcrumbItem({ children }: { children: React.ReactNode }) {
  return <li className="flex items-center gap-1.5">{children}</li>
}

function BreadcrumbLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="text-muted-foreground hover:text-foreground transition-colors">
      {children}
    </Link>
  )
}

function BreadcrumbSeparator() {
  return <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" aria-hidden="true" />
}

function BreadcrumbPage({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-foreground font-medium" aria-current="page">
      {children}
    </span>
  )
}

export { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbSeparator, BreadcrumbPage }
