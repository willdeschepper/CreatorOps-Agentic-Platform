import { test, expect, type Page } from '@playwright/test';
import { randomUUID } from 'node:crypto';
// @ts-expect-error The preparation helper runs only in Node; it is excluded from browser code.
import { api, auth, until, prepareScenario } from '../../scripts/local-scenario.mjs';
async function signIn(page: Page, email: string, creator = false) {
  await page.goto('/login');
  if (creator) await page.getByRole('button', { name: 'Creator', exact: true }).click();
  await page.getByLabel('E-mail').fill(email);
  await page.getByLabel('Senha').fill('CreatorOps123!');
  await page.getByRole('button', { name: 'Entrar no workspace' }).click();
  await expect(page).toHaveURL(/\/app$/);
}
async function confirm(page: Page, title: string, comment?: string) {
  await page.getByRole('button', { name: title, exact: true }).click();
  const dialog = page.getByRole('dialog');
  if (comment) await dialog.getByLabel('Comentário').fill(comment);
  await dialog
    .getByRole('button', { name: `Confirmar: ${title.toLowerCase()}`, exact: true })
    .click();
  await expect(dialog.getByText('Solicitação registrada com sucesso.')).toBeVisible();
  await dialog.getByRole('button', { name: 'Concluir', exact: true }).click();
}
test('programa: termos publicados e plano só da campanha não permitem ativação', async ({
  page,
}) => {
  const suffix = randomUUID().slice(0, 8);
  const owner = await auth('owner@creatorops.dev');
  const program = await api('/v1/programs', owner, {
    name: `Preparação de programa ${suffix}`,
    slug: `preparacao-${suffix}`,
  });
  await api(`/v1/programs/${program.id}/terms`, owner, {
    content: 'Termos obrigatórios para testar a preparação do programa.',
    required: true,
  });
  const campaign = await api(`/v1/programs/${program.id}/campaigns`, owner, {
    name: 'Campanha inicial',
  });
  await api(`/v1/programs/${program.id}/commission-plans`, owner, {
    campaign_id: campaign.id,
    base_rate: '0.10',
    active_from: new Date().toISOString(),
  });
  await signIn(page, 'owner@creatorops.dev');
  await page.goto(`/app/programs/${program.id}`);
  const readiness = page.getByRole('region', { name: 'Preparação do programa' });
  await expect(readiness).toContainText('Não é necessário ativar os termos novamente');
  await expect(readiness).toContainText('Planos de campanha não substituem o padrão');
  await expect(page.getByRole('button', { name: 'Ativar programa', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Planos', exact: true }).click();
  await expect(page.getByRole('columnheader', { name: 'Escopo' })).toBeVisible();
  await expect(page.getByRole('table')).toContainText('Campanha específica');
  await expect(page.getByRole('link', { name: 'Ver campanha' })).toHaveAttribute(
    'href',
    `/app/campaigns/${campaign.id}`,
  );
  await readiness.getByRole('button', { name: 'Criar plano padrão' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog.getByLabel('Campanha')).toHaveCount(0);
  await dialog.getByLabel('Taxa base').fill('0.12');
  const activeFrom = await page.evaluate(() => {
    const now = new Date(Date.now() - 60_000);
    return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
  });
  await dialog.getByLabel('Vigência').fill(activeFrom);
  await dialog.getByRole('button', { name: 'Confirmar: criar plano padrão' }).click();
  await expect(dialog.getByText('Solicitação registrada com sucesso.')).toBeVisible();
  await dialog.getByRole('button', { name: 'Concluir' }).click();
  await expect(readiness).toContainText('Existe um plano sem campanha vinculada');
  await expect(page.getByRole('table')).toContainText('Padrão do programa');
  await expect(page.getByRole('button', { name: 'Ativar programa', exact: true })).toBeEnabled();
  await confirm(page, 'Ativar programa');
  expect((await api(`/v1/programs/${program.id}`, owner)).status).toBe('active');
  const plans = await api(`/v1/programs/${program.id}/commission-plans`, owner);
  expect(
    plans.items.some((item: { campaign_id: string | null }) => item.campaign_id === null),
  ).toBe(true);
});
test('creator: aceite real, novo termo, isolamento e sessão expirada', async ({ page }) => {
  const s = await prepareScenario();
  await signIn(page, s.email, true);
  await expect(page.getByRole('link', { name: 'Pagamentos', exact: true })).toHaveCount(0);
  await page.goto(`/app/memberships/${s.membership.id}`);
  await expect(
    page.locator('.detail-status').getByText('awaiting_terms', { exact: true }),
  ).toBeVisible();
  await confirm(page, 'Aceitar termos vigentes');
  await expect(
    page.getByRole('button', { name: 'Aceitar termos vigentes', exact: true }),
  ).toHaveCount(0);
  const detail = await api(`/v1/memberships/${s.membership.id}`, s.creator);
  expect(detail.status).toBe('active');
  expect(detail.assets.every((a: { active: boolean }) => a.active)).toBe(true);
  await api(`/v1/programs/${s.program.id}/terms`, s.owner, {
    content: 'Nova versão obrigatória dos termos para demonstração local.',
    required: true,
  });
  await page.reload();
  await expect(
    page.locator('.detail-status').getByText('awaiting_terms', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Aceitar termos vigentes', exact: true }),
  ).toBeVisible();
  const other = await prepareScenario();
  await page.goto(`/app/memberships/${other.membership.id}`);
  await expect(page.getByRole('alert')).toContainText('Registro não encontrado');
  await page.evaluate(() =>
    sessionStorage.setItem('creatorops.session.v1', 'invalid-expired-token'),
  );
  await page.goto('/app');
  await expect(page).toHaveURL(/login/);
  expect(await page.evaluate(() => sessionStorage.getItem('creatorops.session.v1'))).toBeNull();
});
test('financeiro: unknown, evidências, gates, aprovação e execução separadas', async ({ page }) => {
  const s = await prepareScenario({ payment: true });
  await signIn(page, 'finance@creatorops.dev');
  await page.goto(`/app/finance/payout-batches/${s.batch.batch.id}`);
  await expect(page.getByText('Resultado desconhecido: a reserva permanece.')).toBeVisible();
  const run = await api('/v1/reconciliation/runs', s.finance, {}, 'POST');
  const findings = await api('/v1/agent/findings?limit=100', s.finance);
  const finding = findings.items.find(
    (f: { payout_id: string }) => f.payout_id === s.batch.payouts[0].id,
  );
  expect(finding).toBeTruthy();
  await page.goto(`/app/agent/findings/${finding.id}`);
  await confirm(page, 'Gerar proposta');
  const proposals = await api(`/v1/agent/proposals?finding_id=${finding.id}`, s.finance);
  const proposal = proposals.items[0];
  await page.goto(`/app/agent/proposals/${proposal.id}`);
  await expect(page.getByRole('button', { name: 'Executar correção', exact: true })).toHaveCount(0);
  await confirm(page, 'Executar gates');
  await expect(page.getByText('provider_confirmation', { exact: true })).toBeVisible();
  await confirm(page, 'Aprovar proposta', 'Evidências e valor conferidos na demonstração local.');
  const approved = await api(`/v1/agent/proposals/${proposal.id}`, s.finance);
  expect(approved.state).toBe('approved');
  expect(approved.executed_at).toBeNull();
  expect((await api(`/v1/payout-batches/${s.batch.batch.id}`, s.finance)).payouts[0].status).toBe(
    'unknown',
  );
  await confirm(page, 'Executar correção');
  expect((await api(`/v1/payout-batches/${s.batch.batch.id}`, s.finance)).payouts[0].status).toBe(
    'confirmed',
  );
  await expect(page.getByRole('button', { name: 'Executar correção', exact: true })).toHaveCount(0);
  await page.screenshot({ path: 'test-results/proposal-desktop.png', fullPage: true });
});
test('conteúdo: worker, revisão e reimportação preservam decisão', async ({ page }) => {
  const s = await prepareScenario({ payment: true });
  const post = {
    network: 'instagram',
    external_post_id: `post-${s.program.id}`,
    program_id: s.program.id,
    handle: s.handle,
    published_at: new Date().toISOString(),
    metrics: { views: 100 },
  };
  await api('/v1/listening/imports', s.owner, { posts: [post] });
  const first = await until(
    () => api(`/v1/posts?program_id=${s.program.id}`, s.owner),
    (v: { items: unknown[] }) => v.items.length > 0,
  );
  const id = first.items[0].id;
  await signIn(page, 'ops@creatorops.dev');
  await page.goto(`/app/posts/${id}`);
  await confirm(page, 'Aprovado');
  const reviewed = await api(`/v1/posts/${id}`, s.owner);
  expect(reviewed.reviewed_by).toBeTruthy();
  await api('/v1/listening/imports', s.owner, { posts: [{ ...post, metrics: { views: 400 } }] });
  const updated = await until(
    () => api(`/v1/posts/${id}`, s.owner),
    (v: { metrics: { views: number } }) => v.metrics.views === 400,
  );
  expect(updated.status).toBe('approved');
  expect(updated.reviewed_by).toBe(reviewed.reviewed_by);
  await page.reload();
  await expect(page.locator('.detail-status').getByText('approved', { exact: true })).toBeVisible();
  await expect(page.getByText('400', { exact: true })).toBeVisible();
  await page.screenshot({ path: 'test-results/content-desktop.png', fullPage: true });
  await page.goto('/app/posts');
  await page.getByRole('button', { name: 'Importar conteúdo', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Carregar arquivo JSON local (opcional)').setInputFiles({
    name: 'reimportacao.json',
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify({ posts: [{ ...post, handle: 'escopo-alterado' }] })),
  });
  await dialog.getByRole('button', { name: 'Confirmar: importar conteúdo' }).click();
  await expect(dialog.getByRole('alert')).toContainText('O estado mudou');
  await expect(dialog.getByRole('button', { name: 'Recarregar estado' })).toBeVisible();
});
test('operação: criação, campanha, seleção e convite por token', async ({ page }) => {
  const s = await prepareScenario();
  await api(`/v1/memberships/${s.membership.id}/terms-acceptances`, s.creator, {
    terms_id: s.terms.id,
  });
  await signIn(page, 'owner@creatorops.dev');
  await page.goto(`/app/programs/${s.program.id}`);
  await page.getByRole('button', { name: 'Criar campanha', exact: true }).click();
  let dialog = page.getByRole('dialog');
  await dialog.getByLabel('Nome', { exact: false }).fill('Campanha da interface');
  await dialog.getByLabel('Briefing').fill('Uma campanha local criada pela interface.');
  await dialog.getByRole('button', { name: 'Confirmar: criar campanha' }).click();
  await expect(dialog.getByText('Solicitação registrada com sucesso.')).toBeVisible();
  await dialog.getByRole('button', { name: 'Concluir', exact: true }).click();
  await page.getByRole('button', { name: 'Campanhas', exact: true }).click();
  await page.getByRole('link', { name: 'Campanha da interface', exact: true }).click();
  await page.getByRole('button', { name: 'Participantes', exact: true }).click();
  await page.getByRole('button', { name: 'Selecionar creators', exact: true }).click();
  await page.getByLabel(`Creator UI ${s.email.slice(3, 11)}`, { exact: false }).check();
  await confirm(page, 'Confirmar seleção (1)');
  await expect(page.getByText('selected', { exact: true })).toBeVisible();
  const inviteEmail = `invite-${s.program.slug}@creatorops.dev`;
  await api('/v1/auth/register', null, {
    email: inviteEmail,
    password: 'CreatorOps123!',
    display_name: 'Creator Convidado',
  });
  await page.goto(`/app/programs/${s.program.id}`);
  await page.getByRole('button', { name: 'Convidar creator', exact: true }).click();
  dialog = page.getByRole('dialog');
  await dialog.getByLabel('E-mail').fill(inviteEmail);
  await dialog.getByRole('button', { name: 'Confirmar: convidar creator' }).click();
  await expect(
    dialog.getByText('Copie o convite agora. Ele só aparece nesta resposta.'),
  ).toBeVisible();
  const inviteUrl = await dialog.locator('.copyable').getAttribute('title');
  expect(inviteUrl).toContain('/invite/');
  await dialog.getByRole('button', { name: 'Concluir', exact: true }).click();
  await page.getByRole('button', { name: 'Sair da sessão' }).click();
  await signIn(page, inviteEmail, true);
  await page.goto(inviteUrl!);
  await confirm(page, 'Aceitar convite');
  await expect(page.getByText('pending', { exact: true })).toHaveCount(0);
});
