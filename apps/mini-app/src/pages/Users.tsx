import { useState } from 'react';

import { ApiError } from '../lib/api';
import { formatRelative } from '../lib/format';
import { atLeast, ROLE_LABELS } from '../lib/roles';
import { useAuth } from '../hooks/useAuth';
import { useChangeRole, useCreateUser, useUsers } from '../hooks/useUsers';
import { useToast } from '../hooks/useToast';
import { PlusIcon } from '../components/icons';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { PageTitle } from '../components/PageTitle';
import { SkeletonList } from '../components/Skeleton';
import { Button, Card, Field, Input, Select } from '../components/ui';
import type { Role, User } from '../types/contracts';

/** Roles the current actor is allowed to assign (backend also enforces). */
function assignableRoles(actor: Role): Role[] {
  if (actor === 'OWNER') return ['ADMIN', 'OPERATOR', 'VIEWER'];
  if (actor === 'ADMIN') return ['OPERATOR', 'VIEWER'];
  return [];
}

export function Users(): JSX.Element {
  const { user } = useAuth();
  const actorRole = user?.role ?? 'VIEWER';
  const roleOptions = assignableRoles(actorRole);
  const { data, isLoading, isError, error, refetch } = useUsers(true);
  const createUser = useCreateUser();
  const changeRole = useChangeRole();
  const toast = useToast();

  const [showAdd, setShowAdd] = useState(false);
  const [tgId, setTgId] = useState('');
  const [firstName, setFirstName] = useState('');
  const [newRole, setNewRole] = useState<Role>('OPERATOR');

  const submitAdd = async (): Promise<void> => {
    const id = Number(tgId);
    if (!Number.isInteger(id) || id <= 0) {
      toast.show('Укажите корректный Telegram ID (число).', 'error');
      return;
    }
    try {
      await createUser.mutateAsync({
        telegram_user_id: id,
        role: newRole,
        first_name: firstName.trim() || null,
      });
      toast.show('Пользователь добавлен', 'success');
      setTgId('');
      setFirstName('');
      setShowAdd(false);
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : 'Не удалось добавить.', 'error');
    }
  };

  const onRoleChange = async (target: User, role: Role): Promise<void> => {
    try {
      await changeRole.mutateAsync({ id: target.id, role });
      toast.show(`Роль обновлена: ${ROLE_LABELS[role]}`, 'success');
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : 'Не удалось изменить роль.', 'error');
    }
  };

  return (
    <div className="space-y-4">
      <PageTitle
        title="Пользователи"
        subtitle="Доступ и роли"
        action={
          <Button onClick={() => setShowAdd((v) => !v)} aria-label="Добавить пользователя">
            <PlusIcon size={18} /> Добавить
          </Button>
        }
      />

      {showAdd ? (
        <Card>
          <div className="space-y-3">
            <Field label="Telegram ID" hint="Числовой идентификатор пользователя">
              <Input
                inputMode="numeric"
                value={tgId}
                onChange={(e) => setTgId(e.target.value)}
                placeholder="напр. 123456789"
              />
            </Field>
            <Field label="Имя (необязательно)">
              <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </Field>
            <Field label="Роль">
              <Select value={newRole} onChange={(e) => setNewRole(e.target.value as Role)}>
                {roleOptions.map((r) => (
                  <option key={r} value={r}>
                    {ROLE_LABELS[r]}
                  </option>
                ))}
              </Select>
            </Field>
            <Button block onClick={() => void submitAdd()} disabled={createUser.isPending}>
              Добавить пользователя
            </Button>
          </div>
        </Card>
      ) : null}

      {isLoading ? (
        <SkeletonList rows={4} />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !data || data.length === 0 ? (
        <EmptyState icon="👥" title="Нет пользователей" />
      ) : (
        <ul className="space-y-2" aria-label="Список пользователей">
          {data.map((u) => {
            const isSelf = u.telegram_user_id === user?.telegram_user_id;
            // Can only re-assign roles the actor is allowed to grant, and not to self.
            const canEdit = !isSelf && roleOptions.length > 0 && atLeast(actorRole, 'ADMIN');
            const options = Array.from(new Set([u.role, ...roleOptions]));
            return (
              <li key={u.id}>
                <Card className="p-3">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary dark:bg-accent/15 dark:text-accent"
                      aria-hidden
                    >
                      {(u.first_name ?? u.username ?? '?').slice(0, 1).toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-ink dark:text-surface">
                        {u.first_name ?? u.username ?? `ID ${u.telegram_user_id}`}
                        {isSelf ? <span className="ml-1 text-xs text-ink/40">(вы)</span> : null}
                      </p>
                      <p className="truncate text-xs text-ink/55 dark:text-surface/55">
                        {u.username ? `@${u.username} · ` : ''}ID {u.telegram_user_id}
                      </p>
                      <p className="text-[11px] text-ink/45 dark:text-surface/45">
                        {u.is_active ? 'активен' : 'отключён'} · {formatRelative(u.last_seen_at)}
                      </p>
                    </div>
                    {canEdit ? (
                      <Select
                        value={u.role}
                        onChange={(e) => void onRoleChange(u, e.target.value as Role)}
                        disabled={changeRole.isPending}
                        aria-label={`Роль ${u.first_name ?? u.telegram_user_id}`}
                        className="w-auto min-w-[7rem] py-2 text-sm"
                      >
                        {options.map((r) => (
                          <option key={r} value={r}>
                            {ROLE_LABELS[r]}
                          </option>
                        ))}
                      </Select>
                    ) : (
                      <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-semibold text-primary dark:text-accent">
                        {ROLE_LABELS[u.role]}
                      </span>
                    )}
                  </div>
                </Card>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
