/**
 * Minimal inline SVG icon set (no external icon dependency — keeps the bundle
 * small and CSP-friendly). Every icon inherits `currentColor` and takes a size.
 */
import type { SVGProps } from 'react';

type IconProps = Omit<SVGProps<SVGSVGElement>, 'strokeWidth'> & { size?: number };

function base({
  size = 24,
  strokeWidth = 2,
  ...props
}: IconProps & { strokeWidth?: number }): SVGProps<SVGSVGElement> {
  return {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': true,
    focusable: false,
    ...props,
  };
}

export const HomeIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5 9.5V21h14V9.5" />
    <path d="M9 21v-6h6v6" />
  </svg>
);

export const MusicIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M9 18V5l12-2v13" />
    <circle cx="6" cy="18" r="3" />
    <circle cx="18" cy="16" r="3" />
  </svg>
);

export const CalendarIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <rect x="3" y="4" width="18" height="18" rx="2" />
    <path d="M16 2v4M8 2v4M3 10h18" />
  </svg>
);

export const DevicesIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <rect x="2" y="4" width="14" height="12" rx="2" />
    <path d="M8 20h6M11 16v4" />
    <rect x="18" y="9" width="4" height="11" rx="1" />
  </svg>
);

export const UsersIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <circle cx="9" cy="8" r="3.5" />
    <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
    <path d="M16 5.5a3.5 3.5 0 0 1 0 6.9M21 20c0-2.5-1.4-4.7-3.5-5.6" />
  </svg>
);

export const ListIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
  </svg>
);

export const SettingsIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.2.61.76 1.05 1.42 1.05H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

export const PlayIcon = (p: IconProps): JSX.Element => (
  <svg {...base({ ...p, strokeWidth: 0 })} fill="currentColor">
    <path d="M7 5.5v13a1 1 0 0 0 1.53.85l10-6.5a1 1 0 0 0 0-1.7l-10-6.5A1 1 0 0 0 7 5.5z" />
  </svg>
);

export const PauseIcon = (p: IconProps): JSX.Element => (
  <svg {...base({ ...p, strokeWidth: 0 })} fill="currentColor">
    <rect x="6" y="5" width="4" height="14" rx="1" />
    <rect x="14" y="5" width="4" height="14" rx="1" />
  </svg>
);

export const StopIcon = (p: IconProps): JSX.Element => (
  <svg {...base({ ...p, strokeWidth: 0 })} fill="currentColor">
    <rect x="6" y="6" width="12" height="12" rx="2" />
  </svg>
);

export const PlusIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);

export const MinusIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M5 12h14" />
  </svg>
);

export const UploadIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M12 15V3M7 8l5-5 5 5" />
    <path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4" />
  </svg>
);

export const TrashIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M6 6v14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V6" />
  </svg>
);

export const EditIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M12 20h9" />
    <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />
  </svg>
);

export const CheckIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M20 6 9 17l-5-5" />
  </svg>
);

export const AlertIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
    <path d="M12 9v4M12 17h.01" />
  </svg>
);

export const WifiIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0M2 9a15 15 0 0 1 20 0" />
    <path d="M12 20h.01" />
  </svg>
);

export const WifiOffIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="m2 2 20 20" />
    <path d="M8.5 16a5 5 0 0 1 7 0" />
    <path d="M5 12.5a10 10 0 0 1 4-2.7M2 9a15 15 0 0 1 5-3.2M19 12.5a10 10 0 0 0-2.2-1.6M22 9a15 15 0 0 0-6.6-3.8" />
    <path d="M12 20h.01" />
  </svg>
);

export const VolumeIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M11 5 6 9H3v6h3l5 4V5z" />
    <path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 6a9 9 0 0 1 0 12" />
  </svg>
);

export const CloseIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M18 6 6 18M6 6l12 12" />
  </svg>
);

export const DownloadIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <path d="M12 3v12M7 10l5 5 5-5" />
    <path d="M4 21h16" />
  </svg>
);

export const ClockIcon = (p: IconProps): JSX.Element => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </svg>
);
