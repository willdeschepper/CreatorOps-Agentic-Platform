import type { paths } from '../api/schema';
import type { Action } from '../components/form';
import type { Row } from '../components/data';
import type { Role } from '../app/session';
import { financiers, operators } from '../app/session';
import { label } from '../lib/format';
const transitionMaps: Record<string, Record<string, string[]>> = {
  programs: {
    draft: ['active', 'closed'],
    active: ['paused', 'closed'],
    paused: ['active', 'closed'],
  },
  campaigns: {
    draft: ['scheduled', 'active', 'cancelled'],
    scheduled: ['active', 'cancelled'],
    active: ['ended', 'cancelled'],
  },
  memberships: {
    awaiting_terms: ['offboarded'],
    active: ['paused', 'offboarded'],
    paused: ['active', 'offboarded'],
  },
};
export function detailActions(kind: string, row: Row, role: Role): Action[] {
  const id = String(row.id),
    state = String(row.status ?? row.state),
    ops = operators.includes(role),
    fin = financiers.includes(role);
  const list: Action[] = [];
  const add = (
    title: string,
    path: string,
    contract: keyof paths,
    initial?: Row,
    hidden?: string[],
    description?: string,
  ) => list.push({ title, path, contract, initial, hidden, description });
  if (ops && transitionMaps[kind])
    for (const status of transitionMaps[kind][state] ?? [])
      add(
        kind === 'programs' && status === 'active' ? 'Ativar programa' : label(status),
        `/v1/${kind}/${id}/status`,
        kind === 'programs'
          ? '/v1/programs/{program_id}/status'
          : kind === 'campaigns'
            ? '/v1/campaigns/{campaign_id}/status'
            : '/v1/memberships/{membership_id}/status',
        { status },
        ['status'],
        `Alterar para ${label(status).toLowerCase()}. O servidor verificará os termos, a elegibilidade e o estado atual.`,
      );
  if (kind === 'programs') {
    if (ops) {
      add(
        'Publicar termos',
        `/v1/programs/${id}/terms`,
        '/v1/programs/{program_id}/terms',
        undefined,
        undefined,
        'Uma nova versão obrigatória suspende os assets até cada creator aceitar os termos novamente.',
      );
      add('Criar campanha', `/v1/programs/${id}/campaigns`, '/v1/programs/{program_id}/campaigns');
      add(
        'Convidar creator',
        `/v1/programs/${id}/invitations`,
        '/v1/programs/{program_id}/invitations',
      );
    }
    if (fin)
      add(
        'Criar plano',
        `/v1/programs/${id}/commission-plans`,
        '/v1/programs/{program_id}/commission-plans',
      );
    if (role === 'creator' && state === 'active')
      add(
        'Candidatar-me',
        `/v1/programs/${id}/applications`,
        '/v1/programs/{program_id}/applications',
      );
  }
  if (kind === 'applications' && ['submitted', 'in_review'].includes(state)) {
    if (ops)
      for (const decision of state === 'submitted'
        ? ['in_review', 'approved', 'rejected']
        : ['approved', 'rejected'])
        add(
          label(decision),
          `/v1/applications/${id}/review`,
          '/v1/applications/{application_id}/review',
          { decision },
          ['decision'],
        );
    if (role === 'creator')
      add(
        'Retirar candidatura',
        `/v1/applications/${id}/withdraw`,
        '/v1/applications/{application_id}/withdraw',
      );
  }
  if (
    kind === 'memberships' &&
    role === 'creator' &&
    state === 'awaiting_terms' &&
    row.required_terms
  )
    add(
      'Aceitar termos vigentes',
      `/v1/memberships/${id}/terms-acceptances`,
      '/v1/memberships/{membership_id}/terms-acceptances',
      { terms_id: (row.required_terms as Row).id },
      ['terms_id'],
      'Ao confirmar, você aceita a versão dos termos exibida nesta página.',
    );
  if (kind === 'posts' && ops)
    for (const decision of ['approved', 'rejected'])
      if (decision !== state)
        add(
          label(decision),
          `/v1/posts/${id}/review`,
          '/v1/posts/{content_id}/review',
          { decision },
          ['decision'],
          'A revisão registra seu usuário e a data da decisão. Conteúdo aprovado não gera comissão por si só.',
        );
  if (kind === 'payout-batches' && fin && state === 'draft') {
    add(
      'Aprovar lote',
      `/v1/payout-batches/${id}/approve`,
      '/v1/payout-batches/{batch_id}/approve',
      undefined,
      undefined,
      'A aprovação confere o saldo atual e reserva o valor de todos os payouts do snapshot.',
    );
    add('Cancelar lote', `/v1/payout-batches/${id}/cancel`, '/v1/payout-batches/{batch_id}/cancel');
  }
  if (kind === 'findings' && fin && ['open', 'proposed'].includes(state)) {
    add(
      'Gerar proposta',
      `/v1/agent/findings/${id}/proposals`,
      '/v1/agent/findings/{finding_id}/proposals',
    );
    add(
      'Encerrar manualmente',
      `/v1/agent/findings/${id}/dismiss`,
      '/v1/agent/findings/{finding_id}/dismiss',
      undefined,
      undefined,
      'O encerramento registra o comentário, mas não modifica ledger nem pagamento.',
    );
  }
  if (kind === 'proposals' && fin) {
    if (['draft', 'blocked'].includes(state))
      add(
        'Executar gates',
        `/v1/agent/proposals/${id}/gate`,
        '/v1/agent/proposals/{proposal_id}/gate',
      );
    if (state === 'gated')
      add(
        'Aprovar proposta',
        `/v1/agent/proposals/${id}/approve`,
        '/v1/agent/proposals/{proposal_id}/approve',
        undefined,
        undefined,
        'A aprovação registra sua decisão. A correção só acontece ao solicitar a execução separadamente.',
      );
    if (!['executed', 'rejected'].includes(state))
      add(
        'Rejeitar proposta',
        `/v1/agent/proposals/${id}/reject`,
        '/v1/agent/proposals/{proposal_id}/reject',
      );
    if (state === 'approved' && row.approved_by)
      add(
        'Executar correção',
        `/v1/agent/proposals/${id}/execute`,
        '/v1/agent/proposals/{proposal_id}/execute',
        undefined,
        undefined,
        'O servidor revalidará os gates e a aprovação antes de aplicar a correção financeira auditada.',
      );
  }
  return list;
}
export function listActions(kind: string, role: Role): Action[] {
  if (kind === 'programs' && operators.includes(role))
    return [{ title: 'Novo programa', path: '/v1/programs', contract: '/v1/programs' }];
  if (kind === 'posts' && operators.includes(role))
    return [
      {
        title: 'Importar conteúdo',
        path: '/v1/listening/imports',
        contract: '/v1/listening/imports',
        description:
          'Os posts serão enfileirados para processamento local. Use Atualizar ou Acompanhar para consultar os resultados.',
      },
    ];
  if (financiers.includes(role)) {
    if (kind === 'commissions')
      return [
        {
          title: 'Liquidar comissões',
          path: '/v1/commissions/settle',
          contract: '/v1/commissions/settle',
        },
      ];
    if (kind === 'payout-batches')
      return [{ title: 'Criar lote', path: '/v1/payout-batches', contract: '/v1/payout-batches' }];
    if (kind === 'reconciliation')
      return [
        {
          title: 'Iniciar reconciliação',
          path: '/v1/reconciliation/runs',
          contract: '/v1/reconciliation/runs',
        },
      ];
  }
  return [];
}
