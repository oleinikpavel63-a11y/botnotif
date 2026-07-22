import { useEffect, useState } from 'react';

import { ApiError } from '../lib/api';
import { ALL_ROLES, ROLE_LABELS } from '../lib/roles';
import { useUpsertScenario } from '../hooks/useScenarios';
import { useTracks } from '../hooks/useTracks';
import { useToast } from '../hooks/useToast';
import { Button, Field, Input, Select, Toggle } from './ui';
import { Sheet } from './Sheet';
import type { Role, Scenario } from '../types/contracts';

const COLORS = ['#2F6B4F', '#E9A93B', '#C94B45', '#3A8A5B', '#4B6FB0', '#7A5AA8'];

export interface ScenarioDraft {
  scenario: Scenario | null;
}

export function ScenarioEditSheet({
  draft,
  onClose,
}: {
  draft: ScenarioDraft | null;
  onClose: () => void;
}): JSX.Element {
  const upsert = useUpsertScenario();
  const toast = useToast();
  const { data: tracks } = useTracks();

  const existing = draft?.scenario ?? null;
  const isNew = existing === null;

  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [icon, setIcon] = useState('🎵');
  const [volume, setVolume] = useState(60);
  const [fadeIn, setFadeIn] = useState(0);
  const [fadeOut, setFadeOut] = useState(0);
  const [confirmationRequired, setConfirmationRequired] = useState(true);
  const [trackId, setTrackId] = useState('');
  const [color, setColor] = useState<string | null>(null);
  const [roles, setRoles] = useState<Role[]>(['OWNER', 'ADMIN', 'OPERATOR']);

  useEffect(() => {
    if (draft === null) return;
    if (existing) {
      setCode(existing.code);
      setName(existing.name);
      setIcon(existing.icon || '🎵');
      setVolume(existing.volume);
      setFadeIn(existing.fade_in_seconds);
      setFadeOut(existing.fade_out_seconds);
      setConfirmationRequired(existing.confirmation_required);
      setTrackId(existing.track_id ?? '');
      setColor(existing.color);
      setRoles(existing.allowed_roles);
    } else {
      setCode('');
      setName('');
      setIcon('🎵');
      setVolume(60);
      setFadeIn(0);
      setFadeOut(0);
      setConfirmationRequired(true);
      setTrackId('');
      setColor(null);
      setRoles(['OWNER', 'ADMIN', 'OPERATOR']);
    }
  }, [draft, existing]);

  const toggleRole = (role: Role): void => {
    setRoles((prev) => (prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]));
  };

  const save = async (): Promise<void> => {
    if (!code.trim() || !name.trim()) {
      toast.show('Укажите код и название сценария.', 'error');
      return;
    }
    try {
      await upsert.mutateAsync({
        id: existing?.id,
        payload: {
          code: code.trim(),
          name: name.trim(),
          icon: icon || '🎵',
          volume,
          fade_in_seconds: fadeIn,
          fade_out_seconds: fadeOut,
          confirmation_required: confirmationRequired,
          track_id: trackId || null,
          allowed_roles: roles,
          color,
        },
      });
      toast.show(isNew ? 'Сценарий создан' : 'Сценарий обновлён', 'success');
      onClose();
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : 'Не удалось сохранить.', 'error');
    }
  };

  return (
    <Sheet open={draft !== null} onClose={onClose} labelledBy="scenario-edit-title">
      <h2 id="scenario-edit-title" className="mb-3 text-lg font-bold text-ink dark:text-surface">
        {isNew ? 'Новый сценарий' : 'Изменить сценарий'}
      </h2>
      <div className="max-h-[65vh] space-y-3 overflow-y-auto pr-1">
        <div className="grid grid-cols-[4rem_1fr] gap-3">
          <Field label="Иконка">
            <Input value={icon} onChange={(e) => setIcon(e.target.value)} maxLength={4} className="text-center text-xl" />
          </Field>
          <Field label="Название">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Например, Подъём" />
          </Field>
        </div>
        <Field label="Код" hint={isNew ? 'Уникальный идентификатор, напр. wake_up' : 'Код изменять не рекомендуется'}>
          <Input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="wake_up"
            disabled={!isNew}
          />
        </Field>

        <Field label={`Громкость: ${volume}%`}>
          <input
            type="range"
            min={0}
            max={100}
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            className="w-full accent-primary"
            aria-label="Громкость сценария"
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Fade in (с)">
            <Input
              type="number"
              min={0}
              step={0.5}
              value={fadeIn}
              onChange={(e) => setFadeIn(Number(e.target.value))}
            />
          </Field>
          <Field label="Fade out (с)">
            <Input
              type="number"
              min={0}
              step={0.5}
              value={fadeOut}
              onChange={(e) => setFadeOut(Number(e.target.value))}
            />
          </Field>
        </div>

        <Field label="Трек">
          <Select value={trackId} onChange={(e) => setTrackId(e.target.value)}>
            <option value="">— не выбран —</option>
            {(tracks ?? []).map((t) => (
              <option key={t.id} value={t.id}>
                {t.title}
              </option>
            ))}
          </Select>
        </Field>

        <div>
          <span className="text-sm font-medium text-ink/80 dark:text-surface/80">Цвет</span>
          <div className="mt-1 flex flex-wrap gap-2">
            <button
              type="button"
              aria-label="Без цвета"
              onClick={() => setColor(null)}
              className={[
                'h-8 w-8 rounded-full border-2 text-xs',
                color === null ? 'border-primary' : 'border-black/10 dark:border-white/20',
              ].join(' ')}
            >
              ✕
            </button>
            {COLORS.map((c) => (
              <button
                key={c}
                type="button"
                aria-label={`Цвет ${c}`}
                onClick={() => setColor(c)}
                style={{ backgroundColor: c }}
                className={[
                  'h-8 w-8 rounded-full border-2',
                  color === c ? 'border-ink dark:border-surface' : 'border-transparent',
                ].join(' ')}
              />
            ))}
          </div>
        </div>

        <div>
          <span className="text-sm font-medium text-ink/80 dark:text-surface/80">Доступно ролям</span>
          <div className="mt-1 flex flex-wrap gap-2">
            {ALL_ROLES.map((role) => {
              const active = roles.includes(role);
              return (
                <button
                  key={role}
                  type="button"
                  aria-pressed={active}
                  onClick={() => toggleRole(role)}
                  className={[
                    'rounded-full px-3 py-1.5 text-xs font-semibold ring-1 transition-colors',
                    active
                      ? 'bg-primary text-white ring-primary'
                      : 'bg-transparent text-ink/60 ring-black/15 dark:text-surface/60 dark:ring-white/20',
                  ].join(' ')}
                >
                  {ROLE_LABELS[role]}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="text-sm font-medium text-ink/80 dark:text-surface/80">
            Требовать подтверждение
          </span>
          <Toggle
            checked={confirmationRequired}
            onChange={setConfirmationRequired}
            label="Требовать подтверждение"
          />
        </div>
      </div>

      <Button block className="mt-4" onClick={() => void save()} disabled={upsert.isPending}>
        {isNew ? 'Создать' : 'Сохранить'}
      </Button>
    </Sheet>
  );
}
