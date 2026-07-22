import { expect, test } from '@playwright/test';

import { openApp, setupMocks } from './mocks';

test.describe('Home / панель управления', () => {
  test('панель открывается и показывает устройство', async ({ page }) => {
    await setupMocks(page, { role: 'OWNER', online: true });
    await openApp(page);

    await expect(page.getByTestId('home-panel')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Главные колонки' })).toBeVisible();
    // Status is conveyed by icon + text, not colour alone.
    await expect(page.getByText('В сети')).toBeVisible();
    await expect(page.getByText('Сейчас играет')).toBeVisible();
  });

  test('офлайн-устройство отображается и блокирует команды', async ({ page }) => {
    await setupMocks(page, { role: 'OWNER', online: false });
    await openApp(page);

    await expect(page.getByText('Не в сети')).toBeVisible();
    await expect(page.getByText('Устройство не в сети — команды недоступны.')).toBeVisible();
    // Quick-action buttons are disabled while offline.
    await expect(page.getByRole('button', { name: /Подъём/ })).toBeDisabled();
  });

  test('запуск сценария требует подтверждения', async ({ page }) => {
    const state = await setupMocks(page, { role: 'OWNER', online: true });
    await openApp(page);

    // "Сбор" has confirmation_required = true.
    await page.getByRole('button', { name: /Сбор/ }).click();

    // Confirmation bottom sheet appears.
    const sheet = page.getByRole('dialog');
    await expect(sheet).toBeVisible();
    await expect(sheet.getByText(/Запустить «Сбор»/)).toBeVisible();

    await sheet.getByRole('button', { name: 'Запустить' }).click();

    await expect.poll(() => state.calls.filter((c) => c === 'play').length).toBeGreaterThan(0);
  });

  test('изменение громкости отправляет команду', async ({ page }) => {
    const state = await setupMocks(page, { role: 'OWNER', online: true });
    await openApp(page);

    await page.getByRole('button', { name: 'Громче на 5%' }).click();

    await expect.poll(() => state.calls.includes('volume')).toBe(true);
  });

  test('остановка воспроизведения', async ({ page }) => {
    const state = await setupMocks(page, { role: 'OWNER', online: true, playerState: 'playing' });
    await openApp(page);

    await page.getByRole('button', { name: 'Стоп' }).click();

    await expect.poll(() => state.calls.some((c) => c.startsWith('stop:'))).toBe(true);
  });
});
