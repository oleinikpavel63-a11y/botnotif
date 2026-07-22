import { expect, test } from '@playwright/test';

import { openApp, setupMocks } from './mocks';

test.describe('Ролевой доступ', () => {
  test('оператор не видит раздел «Пользователи»', async ({ page }) => {
    await setupMocks(page, { role: 'OPERATOR', online: true });
    await openApp(page);

    // Open the "Ещё" (More) menu.
    await page.getByRole('button', { name: 'Ещё' }).click();
    const menu = page.getByRole('dialog');
    await expect(menu).toBeVisible();

    // Users / Audit links must not be present for an OPERATOR.
    await expect(menu.getByRole('link', { name: 'Пользователи' })).toHaveCount(0);
    await expect(menu.getByRole('link', { name: 'Журнал' })).toHaveCount(0);
    // Scenarios and Settings remain available.
    await expect(menu.getByRole('link', { name: 'Сценарии' })).toBeVisible();
    await expect(menu.getByRole('link', { name: 'Настройки' })).toBeVisible();
  });

  test('оператор не может открыть /users напрямую (редирект на главную)', async ({ page }) => {
    await setupMocks(page, { role: 'OPERATOR', online: true });
    await openApp(page, '/users');

    // RequireRole redirects OPERATOR back to Home.
    await expect(page.getByTestId('home-panel')).toBeVisible();
  });

  test('администратор видит раздел «Пользователи»', async ({ page }) => {
    await setupMocks(page, { role: 'ADMIN', online: true });
    await openApp(page, '/users');

    await expect(page.getByRole('heading', { name: 'Пользователи' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Добавить' })).toBeVisible();
  });
});
