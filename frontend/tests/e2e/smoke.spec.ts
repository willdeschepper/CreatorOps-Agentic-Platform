import { test, expect, type Page } from '@playwright/test';
const password = 'CreatorOps123!';
async function login(page: Page, role: string) {
  await page.goto('/login');
  await page.getByLabel('E-mail').fill(`${role}@creatorops.dev`);
  await page.getByLabel('Senha').fill(password);
  await page.getByRole('button', { name: 'Entrar no workspace' }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(
    page.getByRole('heading', { name: 'Cada parceria, um próximo passo.' }),
  ).toBeVisible();
}
test('owner: login, dados reais, detalhes e sessão', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('requestfailed', (r) => {
    if (!r.failure()?.errorText.includes('ABORTED'))
      errors.push(`${r.url().split('?')[0]} ${r.failure()?.errorText}`);
  });
  await login(page, 'owner');
  await page.getByRole('link', { name: 'Programas', exact: true }).click();
  await expect(page.getByRole('table')).toBeVisible();
  await expect(page.getByRole('row').nth(1)).toBeVisible();
  await page.getByRole('button', { name: 'Filtros' }).click();
  await page.locator('.filters select').selectOption('active');
  await expect(page).toHaveURL(/program_status=active/);
  await page.reload();
  await expect(page.getByRole('table')).toBeVisible();
  await page.locator('.row-link').first().click();
  await expect(page.getByRole('button', { name: 'Termos', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Termos', exact: true }).click();
  await expect(page.getByRole('table')).toBeVisible();
  await page.getByRole('button', { name: 'Sair da sessão' }).click();
  await expect(page).toHaveURL(/login/);
  await page.goto('/app/orders');
  await expect(page).toHaveURL(/login/);
  expect(errors).toEqual([]);
});
test('login de staff no modo creator orienta a correção sem apagar as credenciais', async ({
  page,
}) => {
  await page.goto('/login');
  await page.getByRole('button', { name: 'Creator', exact: true }).click();
  await page.getByLabel('E-mail').fill('owner@creatorops.dev');
  await page.getByLabel('Senha').fill(password);
  await page.getByRole('button', { name: 'Entrar no workspace' }).click();
  await expect(page.getByRole('alert')).toContainText('Esta conta usa o acesso Equipe da marca');
  await expect(page.getByRole('alert')).not.toContainText('Sessão expirada');
  await expect(page.getByRole('button', { name: 'Recarregar estado' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Equipe da marca' }).click();
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByLabel('E-mail')).toHaveValue('owner@creatorops.dev');
  await expect(page.getByLabel('Senha')).toHaveValue(password);
  await expect(page.getByLabel('Marca')).toHaveValue('creatorops-demo');
  await page.getByRole('button', { name: 'Entrar no workspace' }).click();
  await expect(page).toHaveURL(/\/app$/);
});
for (const role of ['ops', 'finance'])
  test(`${role}: navegação e restrições por papel`, async ({ page }) => {
    await login(page, role);
    await expect(
      page.getByRole('link', { name: role === 'ops' ? 'Conteúdo' : 'Reconciliação', exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', {
        name: role === 'ops' ? 'Lotes de pagamento' : 'Conteúdo',
        exact: true,
      }),
    ).toHaveCount(0);
    await page.goto(role === 'ops' ? '/app/finance/payout-batches' : '/app/posts');
    await expect(page.getByRole('alert')).toContainText('Acesso não permitido');
  });
test('mobile: navegação, redução de movimento e layout sem overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/login');
  await expect(page.getByRole('button', { name: 'Entrar no workspace' })).toBeVisible();
  expect(
    await page.evaluate(() => ({
      width: innerWidth,
      scroll: document.documentElement.scrollWidth,
      overflow: [...document.querySelectorAll('*')]
        .filter(
          (e) => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.table-scroll'),
        )
        .map((e) => e.className)
        .slice(0, 10),
    })),
  ).toMatchObject({ width: 390, scroll: 390, overflow: [] });
  await login(page, 'owner');
  await page.getByRole('button', { name: 'Abrir menu' }).click();
  await page.getByRole('link', { name: 'Programas', exact: true }).click();
  await expect(page.getByRole('table')).toBeVisible();
  expect(
    await page.evaluate(() => ({
      width: innerWidth,
      scroll: document.documentElement.scrollWidth,
      overflow: [...document.querySelectorAll('*')]
        .filter(
          (e) => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.table-scroll'),
        )
        .map((e) => e.className)
        .slice(0, 10),
    })),
  ).toMatchObject({ width: 390, scroll: 390, overflow: [] });
  await page.screenshot({ path: 'test-results/mobile-programs.png', fullPage: true });
});
