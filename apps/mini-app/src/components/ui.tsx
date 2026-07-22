/** Shared, accessible UI primitives with large touch targets. */
import { forwardRef } from 'react';
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react';

import { haptics } from '../lib/telegram';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: 'bg-primary text-white active:bg-[#255a41] disabled:bg-primary/50',
  secondary:
    'bg-white text-ink border border-black/10 active:bg-black/5 dark:bg-white/10 dark:text-surface dark:border-white/10',
  danger: 'bg-danger text-white active:bg-[#b23e39] disabled:bg-danger/50',
  ghost: 'bg-transparent text-primary active:bg-primary/10 dark:text-accent',
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  block?: boolean;
  /** Fire a light haptic tap on press. */
  haptic?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', block, haptic = true, className = '', onClick, children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-base font-semibold',
        'min-h-[48px] transition-colors select-none',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface dark:focus-visible:ring-offset-ink',
        'disabled:cursor-not-allowed disabled:opacity-70',
        block ? 'w-full' : '',
        VARIANT_CLASSES[variant],
        className,
      ].join(' ')}
      onClick={(e) => {
        if (haptic && !rest.disabled) haptics.impact('light');
        onClick?.(e);
      }}
      {...rest}
    >
      {children}
    </button>
  );
});

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  variant?: Variant;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { label, variant = 'secondary', className = '', onClick, children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      aria-label={label}
      title={label}
      className={[
        'inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-xl',
        'transition-colors select-none',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        'disabled:cursor-not-allowed disabled:opacity-60',
        VARIANT_CLASSES[variant],
        className,
      ].join(' ')}
      onClick={(e) => {
        if (!rest.disabled) haptics.impact('light');
        onClick?.(e);
      }}
      {...rest}
    >
      {children}
    </button>
  );
});

export function Card({
  children,
  className = '',
  as: Tag = 'div',
}: {
  children: ReactNode;
  className?: string;
  as?: 'div' | 'section' | 'article';
}): JSX.Element {
  return (
    <Tag
      className={[
        'rounded-card bg-white/90 p-4 shadow-sm ring-1 ring-black/5',
        'dark:bg-white/[0.06] dark:ring-white/10',
        className,
      ].join(' ')}
    >
      {children}
    </Tag>
  );
}

export function SectionTitle({ children }: { children: ReactNode }): JSX.Element {
  return (
    <h2 className="mb-2 mt-1 text-sm font-semibold uppercase tracking-wide text-ink/60 dark:text-surface/60">
      {children}
    </h2>
  );
}

export function Field({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor?: string;
  hint?: string;
  children: ReactNode;
}): JSX.Element {
  return (
    <label htmlFor={htmlFor} className="block space-y-1">
      <span className="text-sm font-medium text-ink/80 dark:text-surface/80">{label}</span>
      {children}
      {hint ? <span className="block text-xs text-ink/50 dark:text-surface/50">{hint}</span> : null}
    </label>
  );
}

const CONTROL_CLASSES =
  'w-full rounded-xl border border-black/10 bg-white px-3 py-3 text-base text-ink ' +
  'placeholder:text-ink/40 focus:border-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ' +
  'dark:bg-white/10 dark:text-surface dark:border-white/15';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className = '', ...rest }, ref) {
    return <input ref={ref} className={[CONTROL_CLASSES, className].join(' ')} {...rest} />;
  },
);

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className = '', children, ...rest }, ref) {
    return (
      <select ref={ref} className={[CONTROL_CLASSES, className].join(' ')} {...rest}>
        {children}
      </select>
    );
  },
);

export function Toggle({
  checked,
  onChange,
  label,
  disabled,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
  disabled?: boolean;
}): JSX.Element {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => {
        haptics.select();
        onChange(!checked);
      }}
      className={[
        'relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50',
        checked ? 'bg-success' : 'bg-black/20 dark:bg-white/20',
      ].join(' ')}
    >
      <span
        className={[
          'inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform',
          checked ? 'translate-x-6' : 'translate-x-1',
        ].join(' ')}
      />
    </button>
  );
}

export function Spinner({ className = '' }: { className?: string }): JSX.Element {
  return (
    <span
      role="status"
      aria-label="Загрузка"
      className={[
        'inline-block h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent',
        className,
      ].join(' ')}
    />
  );
}
