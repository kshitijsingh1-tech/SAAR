import React from 'react';
import { Github, Linkedin, Instagram, Mail } from 'lucide-react';
import { SOCIAL_PLATFORMS } from '../data/contributorsData';

// Platform Main Links
const PLATFORM_LINKS = {
  github: 'https://github.com/aayush',
  linkedin: 'https://linkedin.com/in/aayush',
  instagram: 'https://instagram.com/aayush',
  gmail: 'mailto:aayush@saar.ai?subject=SAAR%20Inquiry'
};

// 1. Authentic Real Platform Logos (Default State)
const RealBrandIcons = {
  github: ({ size = 32 }) => (
    <svg viewBox="0 0 24 24" width={size} height={size} className="real-logo-svg">
      <rect width="24" height="24" rx="6" fill="#181717" />
      <path
        fill="#ffffff"
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 3C7.03 3 3 7.03 3 12c0 3.98 2.58 7.35 6.16 8.54.45.08.62-.2.62-.43v-1.53c-2.51.55-3.04-1.21-3.04-1.21-.41-1.04-1-1.32-1-1.32-.82-.56.06-.55.06-.55.9.06 1.38.93 1.38.93.8 1.38 2.11.98 2.62.75.08-.58.32-.98.57-1.2-2-.23-4.1-1-4.1-4.45 0-.98.35-1.79.93-2.42-.09-.23-.4-1.15.09-2.39 0 0 .76-.24 2.48.92.72-.2 1.49-.3 2.25-.3.76 0 1.53.1 2.25.3 1.72-1.17 2.47-.92 2.47-.92.49 1.24.19 2.15.1 2.39.58.63.92 1.44.92 2.42 0 3.46-2.11 4.22-4.12 4.44.32.28.61.83.61 1.67v2.48c0 .24.16.51.62.43C18.43 19.34 21 15.98 21 12c0-4.97-4.03-9-9-9z"
      />
    </svg>
  ),

  linkedin: ({ size = 32 }) => (
    <svg viewBox="0 0 24 24" width={size} height={size} className="real-logo-svg">
      <rect width="24" height="24" rx="5.5" fill="#0A66C2" />
      <path
        fill="#ffffff"
        d="M19 19h-3v-4.7c0-1.12-.02-2.56-1.56-2.56-1.56 0-1.8 1.22-1.8 2.48V19h-3V9.5h2.9v1.3h.04c.4-.76 1.38-1.56 2.84-1.56 3.04 0 3.6 2 3.6 4.6V19zM6.5 8.2a1.75 1.75 0 1 1 0-3.5 1.75 1.75 0 0 1 0 3.5zm1.5 10.8H5V9.5h3V19z"
      />
    </svg>
  ),

  instagram: ({ size = 32 }) => (
    <svg viewBox="0 0 24 24" width={size} height={size} className="real-logo-svg">
      <defs>
        <radialGradient id="saar-real-ig-grad" cx="20%" cy="110%" r="140%">
          <stop offset="0%" stopColor="#fdf497" />
          <stop offset="10%" stopColor="#fdf497" />
          <stop offset="45%" stopColor="#fd5949" />
          <stop offset="60%" stopColor="#d6249f" />
          <stop offset="90%" stopColor="#285AEB" />
        </radialGradient>
      </defs>
      <rect width="24" height="24" rx="6" fill="url(#saar-real-ig-grad)" />
      <rect x="5.2" y="5.2" width="13.6" height="13.6" rx="4" fill="none" stroke="#ffffff" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="3.4" fill="none" stroke="#ffffff" strokeWidth="1.6" />
      <circle cx="15.8" cy="8.2" r="0.9" fill="#ffffff" />
    </svg>
  ),

  gmail: ({ size = 32 }) => (
    <svg viewBox="0 0 24 24" width={size} height={size} className="real-logo-svg">
      <path d="M4 6.8v10.4c0 .44.36.8.8.8H7V10.5L4 6.8z" fill="#4285F4" />
      <path d="M20 6.8v10.4c0 .44-.36.8-.8.8H17V10.5l3-3.7z" fill="#34A853" />
      <path d="M4 6.8l3 3.7V5.5L4 6.8z" fill="#FBBC05" />
      <path d="M20 6.8l-3 3.7V5.5L20 6.8z" fill="#C5221F" />
      <path d="M17 5.5L12 9.5 7 5.5v5l5 4 5-4V5.5z" fill="#EA4335" />
    </svg>
  )
};

// 2. Lucide Neon Outline Icons (Hover State)
const NeonOutlineIcons = {
  github: Github,
  linkedin: Linkedin,
  instagram: Instagram,
  gmail: Mail
};

export function SocialContributorsNav({
  variant = 'default',
  className = ''
}) {
  return (
    <div className={`social-contributors-bar variant-${variant} ${className}`}>
      <div className="social-neon-icons-row">
        {SOCIAL_PLATFORMS.map((platform) => {
          const RealIcon = RealBrandIcons[platform.id] || RealBrandIcons.github;
          const NeonIcon = NeonOutlineIcons[platform.id] || Github;
          const targetUrl = PLATFORM_LINKS[platform.id] || '#';

          return (
            <a
              key={platform.id}
              href={targetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`social-neon-icon-btn neon-${platform.id}`}
              aria-label={platform.name}
              title={`SAAR Contributors on ${platform.name}`}
            >
              {/* Default Real Logo */}
              <div className="icon-state real-logo-state">
                <RealIcon size={34} />
              </div>

              {/* Hover Neon Outline Logo */}
              <div className="icon-state neon-logo-state">
                <NeonIcon size={32} strokeWidth={1.8} className="lucide-neon-glyph" />
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}



