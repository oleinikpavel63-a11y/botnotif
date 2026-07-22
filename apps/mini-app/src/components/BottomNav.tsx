import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';

import { useAuth } from '../hooks/useAuth';
import { canViewAudit, canViewUsers } from '../lib/roles';
import { haptics } from '../lib/telegram';
import {
  CalendarIcon,
  DevicesIcon,
  HomeIcon,
  ListIcon,
  MusicIcon,
  SettingsIcon,
  UsersIcon,
} from './icons';
import { Sheet } from './Sheet';

interface NavItem {
  to: string;
  label: string;
  icon: (p: { size?: number }) => JSX.Element;
}

const PRIMARY: NavItem[] = [
  { to: '/', label: 'Главная', icon: HomeIcon },
  { to: '/music', label: 'Музыка', icon: MusicIcon },
  { to: '/schedule', label: 'Расписание', icon: CalendarIcon },
  { to: '/devices', label: 'Устройства', icon: DevicesIcon },
];

function tabClass(isActive: boolean): string {
  return [
    'flex flex-1 flex-col items-center justify-center gap-0.5 py-1.5 text-[11px] font-medium',
    'transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-lg',
    isActive ? 'text-primary dark:text-accent' : 'text-ink/50 dark:text-surface/50',
  ].join(' ');
}

export function BottomNav(): JSX.Element {
  const [moreOpen, setMoreOpen] = useState(false);
  const { user } = useAuth();
  const location = useLocation();
  const role = user?.role ?? 'VIEWER';

  const moreLinks: NavItem[] = [
    { to: '/scenarios', label: 'Сценарии', icon: ListIcon },
    ...(canViewUsers(role) ? [{ to: '/users', label: 'Пользователи', icon: UsersIcon }] : []),
    ...(canViewAudit(role) ? [{ to: '/audit', label: 'Журнал', icon: ListIcon }] : []),
    { to: '/settings', label: 'Настройки', icon: SettingsIcon },
  ];

  const moreActive = moreLinks.some((l) => location.pathname === l.to);

  return (
    <>
      <nav
        aria-label="Основная навигация"
        className={[
          'fixed inset-x-0 bottom-0 z-40 flex items-stretch border-t border-black/10 bg-surface/95 backdrop-blur',
          'dark:border-white/10 dark:bg-[#10160f]/95',
          'pb-[env(safe-area-inset-bottom)]',
        ].join(' ')}
      >
        {PRIMARY.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            onClick={() => haptics.select()}
            className={({ isActive }) => tabClass(isActive)}
          >
            {({ isActive }) => (
              <>
                <item.icon size={22} />
                <span>{item.label}</span>
                <span className="sr-only">{isActive ? '(текущая)' : ''}</span>
              </>
            )}
          </NavLink>
        ))}
        <button
          type="button"
          onClick={() => {
            haptics.select();
            setMoreOpen(true);
          }}
          className={tabClass(moreActive)}
          aria-haspopup="dialog"
          aria-expanded={moreOpen}
        >
          <ListIcon size={22} />
          <span>Ещё</span>
        </button>
      </nav>

      <Sheet open={moreOpen} onClose={() => setMoreOpen(false)} labelledBy="more-title">
        <h2 id="more-title" className="mb-3 text-lg font-bold text-ink dark:text-surface">
          Меню
        </h2>
        <div className="grid grid-cols-2 gap-3">
          {moreLinks.map((l) => (
            <MoreLink key={l.to} to={l.to} onNavigate={() => setMoreOpen(false)}>
              <l.icon size={24} />
              <span>{l.label}</span>
            </MoreLink>
          ))}
        </div>
      </Sheet>
    </>
  );
}

function MoreLink({
  to,
  onNavigate,
  children,
}: {
  to: string;
  onNavigate: () => void;
  children: ReactNode;
}): JSX.Element {
  return (
    <NavLink
      to={to}
      onClick={() => {
        haptics.select();
        onNavigate();
      }}
      className={({ isActive }) =>
        [
          'flex flex-col items-center justify-center gap-2 rounded-2xl px-4 py-5 text-sm font-semibold',
          'ring-1 transition-colors',
          isActive
            ? 'bg-primary/10 text-primary ring-primary/30 dark:text-accent'
            : 'bg-white/70 text-ink ring-black/5 dark:bg-white/[0.06] dark:text-surface dark:ring-white/10',
        ].join(' ')
      }
    >
      {children}
    </NavLink>
  );
}
