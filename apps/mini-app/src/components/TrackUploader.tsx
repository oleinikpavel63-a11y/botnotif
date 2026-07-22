import { useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { ApiError } from '../lib/api';
import { AUDIO_EXTENSIONS, MAX_UPLOAD_MB } from '../lib/config';
import { formatBytes } from '../lib/format';
import { qk } from '../lib/queryClient';
import { uploadTrackWithProgress } from '../lib/upload';
import { useToast } from '../hooks/useToast';
import { canPreviewTracks } from '../lib/roles';
import { useAuth } from '../hooks/useAuth';
import { CloseIcon, UploadIcon } from './icons';
import { Button, Card, Field, Input, Toggle } from './ui';

function extensionOf(name: string): string {
  const idx = name.lastIndexOf('.');
  return idx >= 0 ? name.slice(idx + 1).toLowerCase() : '';
}

function validate(file: File): string | null {
  const ext = extensionOf(file.name);
  if (!AUDIO_EXTENSIONS.includes(ext as (typeof AUDIO_EXTENSIONS)[number])) {
    return `Формат .${ext || '?'} не поддерживается. Разрешено: ${AUDIO_EXTENSIONS.join(', ')}.`;
  }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return `Файл слишком большой (${formatBytes(file.size)}). Максимум ${MAX_UPLOAD_MB} МБ.`;
  }
  return null;
}

/** Drag-and-drop / picker upload with validation, preview and progress. */
export function TrackUploader(): JSX.Element {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { user } = useAuth();
  const canPreview = canPreviewTracks(user?.role ?? 'VIEWER');

  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [isAnnouncement, setIsAnnouncement] = useState(false);

  const [progress, setProgress] = useState<number | null>(null);

  const chooseFile = (next: File | null): void => {
    setError(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (!next) {
      setFile(null);
      setPreviewUrl(null);
      return;
    }
    const problem = validate(next);
    if (problem) {
      setError(problem);
      setFile(null);
      setPreviewUrl(null);
      toast.show(problem, 'error');
      return;
    }
    setFile(next);
    setTitle((prev) => prev || next.name.replace(/\.[^.]+$/, ''));
    setPreviewUrl(canPreview ? URL.createObjectURL(next) : null);
  };

  const reset = (): void => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setTitle('');
    setCategory('');
    setIsAnnouncement(false);
    setProgress(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const submit = async (): Promise<void> => {
    if (!file) return;
    setProgress(0);
    try {
      await uploadTrackWithProgress(
        file,
        { title: title.trim() || undefined, category: category.trim() || undefined, isAnnouncement },
        setProgress,
      );
      await queryClient.invalidateQueries({ queryKey: qk.tracks });
      toast.show('Трек загружен', 'success');
      reset();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Не удалось загрузить трек.';
      toast.show(message, 'error');
      setProgress(null);
    }
  };

  const uploading = progress !== null;

  return (
    <Card>
      <input
        ref={inputRef}
        type="file"
        accept={AUDIO_EXTENSIONS.map((e) => `.${e}`).join(',')}
        className="sr-only"
        onChange={(e) => chooseFile(e.target.files?.[0] ?? null)}
      />

      {!file ? (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            chooseFile(e.dataTransfer.files?.[0] ?? null);
          }}
          className={[
            'flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent',
            dragOver
              ? 'border-primary bg-primary/5'
              : 'border-black/15 hover:border-primary/50 dark:border-white/15',
          ].join(' ')}
        >
          <span className="text-primary dark:text-accent" aria-hidden>
            <UploadIcon size={32} />
          </span>
          <span className="text-sm font-semibold text-ink dark:text-surface">
            Перетащите файл или нажмите
          </span>
          <span className="text-xs text-ink/50 dark:text-surface/50">
            {AUDIO_EXTENSIONS.join(', ')} · до {MAX_UPLOAD_MB} МБ
          </span>
        </button>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink dark:text-surface">{file.name}</p>
              <p className="text-xs text-ink/50 dark:text-surface/50">{formatBytes(file.size)}</p>
            </div>
            {!uploading ? (
              <button
                type="button"
                onClick={reset}
                aria-label="Убрать файл"
                className="rounded-lg p-1 text-ink/50 hover:bg-black/5 dark:text-surface/50 dark:hover:bg-white/10"
              >
                <CloseIcon size={20} />
              </button>
            ) : null}
          </div>

          {previewUrl ? (
            <audio controls src={previewUrl} className="w-full" preload="metadata">
              Предпрослушивание недоступно
            </audio>
          ) : null}

          <Field label="Название">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Название трека" />
          </Field>
          <Field label="Категория" hint="Например: гимн, фоновая, объявление">
            <Input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Категория" />
          </Field>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-ink/80 dark:text-surface/80">Объявление</span>
            <Toggle checked={isAnnouncement} onChange={setIsAnnouncement} label="Пометить как объявление" />
          </div>

          {uploading ? (
            <div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-black/10 dark:bg-white/15">
                <div
                  className="h-full rounded-full bg-primary transition-[width] dark:bg-accent"
                  style={{ width: `${Math.round((progress ?? 0) * 100)}%` }}
                />
              </div>
              <p className="mt-1 text-center text-xs text-ink/60 dark:text-surface/60">
                Загрузка… {Math.round((progress ?? 0) * 100)}%
              </p>
            </div>
          ) : (
            <Button block onClick={() => void submit()} disabled={!!error}>
              <UploadIcon size={20} /> Загрузить
            </Button>
          )}
        </div>
      )}

      {error ? (
        <p className="mt-2 text-sm text-danger" role="alert">
          {error}
        </p>
      ) : null}
    </Card>
  );
}
