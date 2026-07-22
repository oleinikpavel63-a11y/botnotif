import { ApiError } from '../lib/api';
import { AlertIcon } from './icons';
import { Button } from './ui';

export function ErrorState({
  error,
  onRetry,
  title = 'Что-то пошло не так',
}: {
  error?: unknown;
  onRetry?: () => void;
  title?: string;
}): JSX.Element {
  const message =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : 'Не удалось загрузить данные.';

  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center rounded-card border border-danger/30 bg-danger/5 px-6 py-8 text-center"
    >
      <span className="mb-2 text-danger" aria-hidden>
        <AlertIcon size={32} />
      </span>
      <p className="text-base font-semibold text-ink dark:text-surface">{title}</p>
      <p className="mt-1 max-w-xs text-sm text-ink/70 dark:text-surface/70">{message}</p>
      {onRetry ? (
        <Button variant="secondary" className="mt-4" onClick={onRetry}>
          Повторить
        </Button>
      ) : null}
    </div>
  );
}
