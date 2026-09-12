// Test/demo preparation only. Never imported by the browser application.
import { createHmac, randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
const origin = 'http://localhost:8000';
export async function api(path, token, body, method = body === undefined ? 'GET' : 'POST') {
  const r = await fetch(origin + path, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(`${method} ${path}: ${r.status} ${data.detail ?? data.code}`);
  return data;
}
export async function auth(email, creator = false) {
  return (
    await api('/v1/auth/token', null, {
      email,
      password: 'CreatorOps123!',
      brand_slug: creator ? null : 'creatorops-demo',
    })
  ).access_token;
}
export async function until(read, predicate) {
  for (let i = 0; i < 80; i++) {
    const v = await read();
    if (predicate(v)) return v;
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error('Worker local não concluiu dentro de 20 segundos.');
}
export async function prepareScenario({ payment = false } = {}) {
  const suffix = randomUUID().slice(0, 8),
    owner = await auth('owner@creatorops.dev'),
    finance = await auth('finance@creatorops.dev');
  const email = `ui-${suffix}@creatorops.dev`,
    handle = `ui_${suffix}`;
  await api('/v1/auth/register', null, {
    email,
    password: 'CreatorOps123!',
    display_name: `Creator UI ${suffix}`,
    socials: [{ network: 'instagram', handle }],
  });
  const creator = await auth(email, true);
  const program = await api('/v1/programs', owner, {
    name: `Parcerias de setembro · ${suffix}`,
    slug: `ui-${suffix}`,
    return_window_days: 0,
    payout_minimum: '1.00',
  });
  const terms = await api(`/v1/programs/${program.id}/terms`, owner, {
    content: 'Termos de demonstração local para teste da jornada de creators.',
    required: true,
  });
  await api(`/v1/programs/${program.id}/commission-plans`, finance, {
    base_rate: '0.10',
    return_window_days: 0,
    payout_minimum: '1.00',
    active_from: new Date(Date.now() - 60000).toISOString(),
  });
  await api(`/v1/programs/${program.id}/status`, owner, { status: 'active' });
  const application = await api(`/v1/programs/${program.id}/applications`, creator, {
    motivation: 'Quero participar desta demonstração local.',
  });
  const reviewed = await api(`/v1/applications/${application.id}/review`, owner, {
    decision: 'approved',
    note: 'Revisão local para teste de interface.',
  });
  const membership = reviewed.membership;
  const state = { owner, finance, creator, email, program, terms, application, membership, handle };
  if (!payment) return state;
  const activation = await api(`/v1/memberships/${membership.id}/terms-acceptances`, creator, {
    terms_id: terms.id,
  });
  const coupon = activation.assets.find((a) => a.asset_type === 'coupon');
  let secret = process.env.COMMERCE_WEBHOOK_SECRET;
  if (!secret) {
    const env = await readFile(new URL('../../.env', import.meta.url), 'utf8').catch(() => '');
    secret =
      env.match(/^COMMERCE_WEBHOOK_SECRET=(.*)$/m)?.[1]?.replace(/^['"]|['"]$/g, '') ??
      'local-commerce-secret';
  }
  const raw = JSON.stringify({
    event_id: `evt-ui-${suffix}`,
    event_type: 'order.paid',
    order_id: `order-ui-${suffix}`,
    occurred_at: new Date().toISOString(),
    amount: '1250.00',
    currency: 'BRL',
    coupon_code: coupon.code,
  });
  const webhook = await fetch(`${origin}/v1/webhooks/commerce/creatorops-demo`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Signature': `sha256=${createHmac('sha256', secret).update(raw).digest('hex')}`,
    },
    body: raw,
  });
  if (!webhook.ok) throw new Error(`Webhook local recusado: ${webhook.status}`);
  await api('/v1/commissions/settle', finance, {
    as_of: new Date(Date.now() + 86400000).toISOString(),
  });
  const batch = await api('/v1/payout-batches', finance, {
    program_id: program.id,
    cutoff_at: new Date(Date.now() + 86460000).toISOString(),
    scenario: 'timeout_after',
  });
  await api(`/v1/payout-batches/${batch.batch.id}/approve`, finance, {
    comment: 'Teste local de timeout após transferência simulada.',
  });
  const completed = await until(
    () => api(`/v1/payout-batches/${batch.batch.id}`, finance),
    (b) => b.payouts.some((p) => p.status === 'unknown'),
  );
  return { ...state, batch: completed };
}
if (process.argv.includes('--prepare')) {
  const s = await prepareScenario({ payment: true });
  console.log(
    JSON.stringify(
      {
        program_id: s.program.id,
        membership_id: s.membership.id,
        creator_email: s.email,
        batch_id: s.batch.batch.id,
        payout_state: 'unknown',
        open: `http://localhost:5173/app/finance/payout-batches/${s.batch.batch.id}`,
      },
      null,
      2,
    ),
  );
}
