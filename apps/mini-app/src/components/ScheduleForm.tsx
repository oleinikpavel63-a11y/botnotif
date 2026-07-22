import { useState } from 'react';

import { ApiError } from '../lib/api';
import { TIMEZONE } from '../lib/config';
import { WEEKDAY_OPTIONS } from '../lib/format';
import { useCreateSchedule } from '../hooks/useSchedules';
import { useToast } from '../hooks/useToast';
import { Button, Field, Input, Select } from './ui';
import { Sheet } from './Sheet';
import type { Device, RecurrenceType, Scenario } from '../types/contracts';

export function ScheduleForm({
  open,
  onClose,
  devices,
  scenarios,
}: {
  open: boolean;
  onClose: () => void;
  devices: Device[];
  scenarios: Scenario[];
}): JSX.Element {
  const create = useCreateSchedule();
  const toast = useToast();

  const [name, setName] = useState('');
  const [scenarioId, setScenarioId] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [recurrence, setRecurrence] = useState<RecurrenceType>('daily');
  const [time, setTime] = useState('07:30');
  const [date, setDate] = useState('');
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4]);

  const toggleDay = (d: number): void => {
    setDays((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d].sort()));
  };

  const submit = async (): Promise<void> => {
    if (!name.trim() || !scenarioId || !deviceId) {
      toast.show('Заполните название, сценарий и устройство.', 'error');
      return;
    }
    if (recurrence === 'once' && !date) {
      toast.show('Укажите дату.', 'error');
      return;
    }
    if (recurrence === 'weekly' && days.length === 0) {
      toast.show('Выберите хотя бы один день недели.', 'error');
      return;
    }
    try {
      await create.mutateAsync({
        name: name.trim(),
        scenario_id: scenarioId,
        device_id: deviceId,
        recurrence_type: recurrence,
        config: {
          time,
          days: recurrence === 'weekly' ? days : null,
          date: recurrence === 'once' ? date : null,
        },
      });
      toast.show('Расписание создано', 'success');
      onClose();
      setName('');
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : 'Не удалось создать.', 'error');
    }
  };

  return (
    <Sheet open={open} onClose={onClose} labelledBy="schedule-form-title">
      <h2 id="schedule-form-title" className="mb-1 text-lg font-bold text-ink dark:text-surface">
        Новое расписание
      </h2>
      <p className="mb-3 text-xs text-ink/50 dark:text-surface/50">Часовой пояс: {TIMEZONE}</p>

      <div className="max-h-[65vh] space-y-3 overflow-y-auto pr-1">
        <Field label="Название">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Например, Утренний подъём" />
        </Field>

        <Field label="Сценарий">
          <Select value={scenarioId} onChange={(e) => setScenarioId(e.target.value)}>
            <option value="">— выберите —</option>
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.icon} {s.name}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Устройство">
          <Select value={deviceId} onChange={(e) => setDeviceId(e.target.value)}>
            <option value="">— выберите —</option>
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Повтор">
          <Select value={recurrence} onChange={(e) => setRecurrence(e.target.value as RecurrenceType)}>
            <option value="once">Однократно</option>
            <option value="daily">Ежедневно</option>
            <option value="weekly">Еженедельно</option>
          </Select>
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Время">
            <Input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
          </Field>
          {recurrence === 'once' ? (
            <Field label="Дата">
              <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </Field>
          ) : null}
        </div>

        {recurrence === 'weekly' ? (
          <div>
            <span className="text-sm font-medium text-ink/80 dark:text-surface/80">Дни недели</span>
            <div className="mt-1 flex flex-wrap gap-2">
              {WEEKDAY_OPTIONS.map(({ label, index }) => {
                const active = days.includes(index);
                return (
                  <button
                    key={index}
                    type="button"
                    aria-pressed={active}
                    onClick={() => toggleDay(index)}
                    className={[
                      'h-10 w-10 rounded-full text-xs font-semibold ring-1 transition-colors',
                      active
                        ? 'bg-primary text-white ring-primary'
                        : 'bg-transparent text-ink/60 ring-black/15 dark:text-surface/60 dark:ring-white/20',
                    ].join(' ')}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>

      <Button block className="mt-4" onClick={() => void submit()} disabled={create.isPending}>
        Создать
      </Button>
    </Sheet>
  );
}
