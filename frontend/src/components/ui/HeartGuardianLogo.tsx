import { type SVGProps, useId } from 'react'

type LogoProps = SVGProps<SVGSVGElement> & {
  size?: number | string
}

export function HeartGuardianLogo({ size = 24, className, ...props }: LogoProps) {
  const uid = useId()
  const gradientId = `hg-grad-${uid}`
  const highlightId = `hg-hi-${uid}`

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      className={className}
      {...props}
    >
      <defs>
        {/* Rose → Blue brand gradient */}
        <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f43f5e" />
          <stop offset="50%" stopColor="#a855f7" />
          <stop offset="100%" stopColor="#3b82f6" />
        </linearGradient>
        {/* Top-left highlight for depth */}
        <radialGradient id={highlightId} cx="0.3" cy="0.3" r="0.7">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
      </defs>
      {/* Heart base with gradient */}
      <path
        d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5
           2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09
           C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5
           c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
        fill={`url(#${gradientId})`}
      />
      {/* Highlight layer for Apple-style depth */}
      <path
        d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5
           2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09
           C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5
           c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
        fill={`url(#${highlightId})`}
      />
      {/* Pulse/ECG line */}
      <path
        d="M4 12h3.5l1.5-3 2 6 2-6 1.5 3H19"
        fill="none"
        stroke="white"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.92"
      />
    </svg>
  )
}
