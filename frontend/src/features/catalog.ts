import type { paths } from '../api/schema';
import type { ReactNode } from 'react';
import type { Role } from '../app/session';
import { financiers, operators, staff } from '../app/session';
export type Collection = {
  title: string;
  description: string;
  endpoint: string;
  contract: keyof paths;
  columns: string[];
  roles: Role[];
  detail?: string;
  poll?: boolean;
  columnLabels?: Record<string, string>;
  renderCell?: (row: Record<string, unknown>, column: string) => ReactNode | undefined;
};
export const collections: Record<string, Collection> = {
  programs: {
    title: 'Programas',
    description: 'O ponto de partida de cada parceria. Termos, regras e creators em um só lugar.',
    endpoint: '/v1/programs',
    contract: '/v1/programs',
    columns: ['name', 'status', 'currency', 'payout_minimum', 'created_at'],
    roles: [...staff, 'creator'],
    detail: 'programs',
  },
  applications: {
    title: 'Candidaturas',
    description: 'Conheça quem quer criar com a marca e acompanhe cada decisão.',
    endpoint: '/v1/applications',
    contract: '/v1/applications',
    columns: ['program_name', 'creator', 'status', 'created_at'],
    roles: [...operators, 'creator'],
    detail: 'applications',
  },
  posts: {
    title: 'Conteúdo',
    description:
      'Identificar é o primeiro passo. A revisão humana transforma conteúdo em resultado.',
    endpoint: '/v1/posts',
    contract: '/v1/posts',
    columns: ['external_post_id', 'network', 'status', 'published_at', 'metrics'],
    roles: operators,
    detail: 'posts',
    poll: true,
  },
  orders: {
    title: 'Vendas',
    description:
      'Cada pedido com seus sinais, sua atribuição e o histórico que explica a comissão.',
    endpoint: '/v1/orders',
    contract: '/v1/orders',
    columns: ['external_id', 'status', 'gross_amount', 'refunded_amount', 'paid_at'],
    roles: staff,
    detail: 'orders',
  },
  commissions: {
    title: 'Comissões',
    description: 'Da venda atribuída ao saldo disponível. Os ajustes preservam o histórico.',
    endpoint: '/v1/commissions',
    contract: '/v1/commissions',
    columns: ['id', 'kind', 'status', 'amount', 'eligible_at', 'membership_id'],
    roles: financiers,
  },
  ledger: {
    title: 'Histórico financeiro',
    description:
      'Lançamentos imutáveis. Cada correção é uma nova entrada, com origem e rastreabilidade.',
    endpoint: '/v1/ledger-entries',
    contract: '/v1/ledger-entries',
    columns: ['created_at', 'bucket', 'entry_type', 'amount', 'description'],
    roles: financiers,
  },
  'payout-batches': {
    title: 'Lotes de pagamento',
    description: 'Revise o snapshot, aprove a reserva e acompanhe a resposta do provedor local.',
    endpoint: '/v1/payout-batches',
    contract: '/v1/payout-batches',
    columns: ['id', 'status', 'cutoff_at', 'approved_by', 'created_at'],
    roles: financiers,
    detail: 'finance/payout-batches',
    poll: true,
  },
  payouts: {
    title: 'Pagamentos',
    description: 'Um resultado desconhecido mantém o saldo reservado até a reconciliação.',
    endpoint: '/v1/payouts',
    contract: '/v1/payouts',
    columns: ['id', 'status', 'amount', 'membership_id', 'provider_reference'],
    roles: financiers,
    poll: true,
  },
  reconciliation: {
    title: 'Reconciliação',
    description: 'Compare evidências e acompanhe as divergências antes de qualquer correção.',
    endpoint: '/v1/reconciliation/runs',
    contract: '/v1/reconciliation/runs',
    columns: ['id', 'status', 'started_at', 'completed_at', 'summary'],
    roles: financiers,
    detail: 'finance/reconciliation',
    poll: true,
  },
  findings: {
    title: 'Divergências',
    description: 'Fatos e evidências preservados para uma decisão informada.',
    endpoint: '/v1/agent/findings',
    contract: '/v1/agent/findings',
    columns: ['finding_type', 'state', 'payout_id', 'created_at'],
    roles: financiers,
    detail: 'agent/findings',
  },
  proposals: {
    title: 'Propostas',
    description: 'Evidência, validação, aprovação e execução. Cada etapa tem seu próprio momento.',
    endpoint: '/v1/agent/proposals',
    contract: '/v1/agent/proposals',
    columns: ['action', 'state', 'risk', 'created_at'],
    roles: financiers,
    detail: 'agent/proposals',
  },
  audit: {
    title: 'Auditoria',
    description: 'As decisões da operação, com ator, entidade e momento.',
    endpoint: '/v1/audit-logs',
    contract: '/v1/audit-logs',
    columns: ['created_at', 'action', 'actor_user_id', 'entity_type', 'entity_id'],
    roles: staff,
  },
};
export const routeCollection = (pathname: string) =>
  collections[pathname.split('/').filter(Boolean).pop() ?? ''];
export function ownCollection(key: string, creator: boolean): Collection {
  if (key === 'applications' && creator)
    return {
      ...collections.applications,
      endpoint: '/v1/applications/me',
      contract: '/v1/applications/me',
      columns: ['program_name', 'status', 'motivation', 'created_at'],
    };
  return collections[key];
}
