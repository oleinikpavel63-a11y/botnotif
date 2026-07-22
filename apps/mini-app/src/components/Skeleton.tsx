/** Shimmering skeleton placeholder blocks. */
export function Skeleton({ className = '' }: { className?: string }): JSX.Element {
  return (
    <div
      aria-hidden
      className={[
        'relative overflow-hidden rounded-lg bg-black/10 dark:bg-white/10',
        'after:absolute after:inset-0 after:-translate-x-full after:animate-shimmer',
        'after:bg-gradient-to-r after:from-transparent after:via-white/40 after:to-transparent',
        'dark:after:via-white/10',
        className,
      ].join(' ')}
    />
  );
}

export function SkeletonCard(): JSX.Element {
  return (
    <div className="rounded-card bg-white/90 p-4 ring-1 ring-black/5 dark:bg-white/[0.06] dark:ring-white/10">
      <div className="flex items-center gap-3">
        <Skeleton className="h-12 w-12 rounded-xl" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      </div>
    </div>
  );
}

export function SkeletonList({ rows = 3 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-3" role="status" aria-label="Загрузка">
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
