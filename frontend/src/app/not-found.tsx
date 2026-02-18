import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Home } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-center p-4">
      <div className="space-y-6">
        <h1 className="text-7xl font-bold text-primary">404</h1>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-foreground">Page not found</h2>
          <p className="text-muted-foreground text-sm max-w-md">
            The page you are looking for does not exist or has been moved.
          </p>
        </div>
        <Link href="/">
          <Button className="mt-4">
            <Home className="w-4 h-4 mr-2" />
            Go Home
          </Button>
        </Link>
      </div>
    </div>
  )
}
