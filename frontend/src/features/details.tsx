import { useQuery } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { resourceOptions, type Page } from '../api/client';
import type { Role } from '../app/session';
import { operators, staff } from '../app/session';
import { ActionButton } from '../components/form';
import { CollectionView } from '../components/collection';
import { Button } from '../components/ui/button';
import {
  DataTable,
  Empty,
  ErrorState,
  Heading,
  Loading,
  Notice,
  RecordDetails,
  Status,
  type Row,
} from '../components/data';
import { detailActions } from './actions';
import { collections, type Collection } from './catalog';
import { Report } from './reports';
import { ProgramReadiness, useProgramReadiness } from './program-readiness';
const detailEndpoints: Record<string, string> = {
  programs: 'programs',
  campaigns: 'campaigns',
  applications: 'applications',
  memberships: 'memberships',
  posts: 'posts',
  orders: 'orders',
  'payout-batches': 'payout-batches',
  reconciliation: 'reconciliation/runs',
  findings: 'agent/findings',
  proposals: 'agent/proposals',
  'commission-plans': 'commission-plans',
};
const titles: Record<string, string> = {
  programs: 'Programa',
  campaigns: 'Campanha',
  applications: 'Candidatura',
  memberships: 'Parceria',
  posts: 'Conteúdo',
  orders: 'Venda',
  'payout-batches': 'Lote de pagamento',
  reconciliation: 'Reconciliação',
  findings: 'Divergência',
  proposals: 'Proposta',
  'commission-plans': 'Plano de comissão',
};
export function DetailPage({ kind, id, role }: { kind: string; id: string; role: Role }) {
  const [tab, setTab] = useState('overview');
  const q = useQuery(
    resourceOptions<Row>(`/v1/${detailEndpoints[kind]}/${encodeURIComponent(id)}`),
  );
  const showReadiness =
    kind === 'programs' &&
    staff.includes(role) &&
    ['draft', 'paused'].includes(String(q.data?.status));
  const readiness = useProgramReadiness(id, showReadiness);
  if (q.isPending) return <Loading />;
  if (q.error) return <ErrorState error={q.error} retry={() => void q.refetch()} />;
  const data = q.data;
  const row = (data.batch ?? data) as Row;
  const ops = operators.includes(role);
  const actions = detailActions(kind, row, role).map((action) =>
    kind === 'programs' && action.initial?.status === 'active' && showReadiness
      ? {
          ...action,
          disabled:
            readiness.isPending ||
            readiness.isFetching ||
            !!readiness.error ||
            !readiness.data?.terms ||
            !readiness.data?.defaultPlan,
        }
      : action,
  );
  const tabs = [
    { key: 'overview', title: 'Visão geral' },
    ...(kind === 'programs'
      ? [
          { key: 'terms', title: 'Termos' },
          { key: 'plans', title: 'Planos' },
          { key: 'campaigns', title: 'Campanhas' },
          ...(ops
            ? [
                { key: 'memberships', title: 'Parcerias' },
                { key: 'invitations', title: 'Convites' },
              ]
            : []),
        ]
      : []),
    ...(kind === 'campaigns' && ops ? [{ key: 'participants', title: 'Participantes' }] : []),
    ...(kind === 'memberships' ? [{ key: 'commissions', title: 'Comissões' }] : []),
    ...((['programs', 'campaigns'].includes(kind) && staff.includes(role)) || kind === 'memberships'
      ? [{ key: 'report', title: 'Resultados' }]
      : []),
  ];
  let config: Collection | undefined;
  if (kind === 'programs') {
    const base = `/v1/programs/${id}`;
    if (tab === 'terms')
      config = {
        title: 'Termos versionados',
        description: '',
        endpoint: `${base}/terms`,
        contract: '/v1/programs/{program_id}/terms',
        columns: ['version', 'content', 'required', 'published_at'],
        roles: [],
      };
    if (tab === 'plans')
      config = {
        title: 'Planos de comissão',
        description: '',
        endpoint: `${base}/commission-plans`,
        contract: '/v1/programs/{program_id}/commission-plans',
        columns: ['version', 'base_rate', 'campaign_id', 'active_from'],
        columnLabels: { campaign_id: 'Escopo' },
        renderCell: (plan, column) =>
          column === 'campaign_id' ? (
            <span className="plan-scope">
              <strong>{plan.campaign_id ? 'Campanha específica' : 'Padrão do programa'}</strong>
              {plan.campaign_id ? (
                <Link to={`/app/campaigns/${plan.campaign_id}`}>Ver campanha ↗</Link>
              ) : (
                <small>Sem campanha vinculada</small>
              )}
            </span>
          ) : undefined,
        roles: [],
        detail: 'commission-plans',
      };
    if (tab === 'campaigns')
      config = {
        title: 'Campanhas',
        description: '',
        endpoint: `${base}/campaigns`,
        contract: '/v1/programs/{program_id}/campaigns',
        columns: ['name', 'status', 'starts_at', 'ends_at'],
        roles: [],
        detail: 'campaigns',
      };
    if (tab === 'memberships')
      config = {
        title: 'Parcerias',
        description: '',
        endpoint: `${base}/memberships`,
        contract: '/v1/programs/{program_id}/memberships',
        columns: ['id', 'creator', 'status', 'activated_at'],
        roles: [],
        detail: 'memberships',
      };
    if (tab === 'invitations')
      config = {
        title: 'Convites',
        description: '',
        endpoint: `${base}/invitations`,
        contract: '/v1/programs/{program_id}/invitations',
        columns: ['email', 'status', 'expires_at', 'used_at'],
        roles: [],
      };
  }
  if (kind === 'campaigns' && tab === 'participants')
    config = {
      title: 'Participantes',
      description: '',
      endpoint: `/v1/campaigns/${id}/participants`,
      contract: '/v1/campaigns/{campaign_id}/participants',
      columns: ['creator', 'status', 'selected_at', 'assets'],
      roles: [],
    };
  if (kind === 'memberships' && tab === 'commissions')
    config = {
      ...collections.commissions,
      endpoint: `/v1/memberships/${id}/commissions`,
      contract: '/v1/memberships/{membership_id}/commissions',
    };
  return (
    <>
      <Link className="back-link" to="/app">
        <ArrowLeft size={15} />
        Workspace
      </Link>
      <Heading
        eyebrow={`WORKSPACE / ${titles[kind]?.toUpperCase()}`}
        title={String(row.name ?? row.program_name ?? row.external_id ?? titles[kind])}
        description={kind === 'proposals' ? String(row.rationale) : undefined}
      >
        <div className="detail-actions">
          {actions.map((action) => (
            <ActionButton key={action.title} action={action} />
          ))}
        </div>
      </Heading>
      {row.status || row.state ? (
        <div className="detail-status">
          <Status value={String(row.status ?? row.state)} />
        </div>
      ) : null}
      {showReadiness ? <ProgramReadiness programId={id} role={role} result={readiness} /> : null}
      {kind === 'proposals' ? (
        <>
          <div className="decision-path">
            {['Evidência', 'Gates', 'Aprovação humana', 'Execução auditada'].map((s, i) => (
              <div key={s}>
                <span>0{i + 1}</span>
                {s}
              </div>
            ))}
          </div>
          <Notice>
            Aprovar registra a decisão. Executar revalida os gates e aplica a correção em uma ação
            separada.
          </Notice>
        </>
      ) : null}
      {kind === 'payout-batches' && (data.payouts as Row[]).some((p) => p.status === 'unknown') ? (
        <Notice>
          <strong>Resultado desconhecido: a reserva permanece.</strong> Não envie outro pagamento.{' '}
          <Link to="/app/finance/reconciliation">Iniciar reconciliação →</Link>
        </Notice>
      ) : null}
      {kind === 'posts' ? (
        <Notice>
          Matching identifica o vínculo; a revisão registra a decisão humana. Reimportações
          preservam status e revisor, e não geram comissão.
        </Notice>
      ) : null}
      {tabs.length > 1 ? (
        <nav className="tabs" aria-label="Seções do detalhe">
          {tabs.map((t) => (
            <button
              key={t.key}
              className={tab === t.key ? 'active' : ''}
              onClick={() => setTab(t.key)}
              aria-current={tab === t.key ? 'page' : undefined}
            >
              {t.title}
            </button>
          ))}
        </nav>
      ) : null}
      {tab === 'overview' ? (
        <section className="panel detail-panel">
          <RecordDetails data={data} />
        </section>
      ) : null}
      {config ? (
        <CollectionView
          key={tab}
          config={config}
          scope={tab}
          actions={
            tab === 'participants' ? (
              <ParticipantPicker campaignId={id} programId={String(row.program_id)} />
            ) : undefined
          }
          rowActions={
            tab === 'invitations'
              ? (r) =>
                  r.status === 'pending' ? (
                    <ActionButton
                      action={{
                        title: 'Revogar',
                        path: `/v1/invitations/${r.id}/revoke`,
                        contract: '/v1/invitations/{invitation_id}/revoke',
                      }}
                    />
                  ) : null
              : tab === 'participants'
                ? (r) => (
                    <ActionButton
                      action={{
                        title: r.status === 'selected' ? 'Remover' : 'Retomar',
                        path: `/v1/campaigns/${id}/participants/${r.membership_id}/status`,
                        contract: '/v1/campaigns/{campaign_id}/participants/{membership_id}/status',
                        initial: { status: r.status === 'selected' ? 'removed' : 'selected' },
                        hidden: ['status'],
                      }}
                    />
                  )
                : undefined
          }
        />
      ) : null}
      {tab === 'report' ? <Report endpoint={`/v1/reports/${kind}/${id}/overview`} /> : null}
      {kind === 'findings' ? (
        <CollectionView
          config={{ ...collections.proposals, endpoint: `/v1/agent/proposals?finding_id=${id}` }}
          hideFilters={['finding_id']}
          scope="finding_proposals"
        />
      ) : null}
    </>
  );
}
function ParticipantPicker({ campaignId, programId }: { campaignId: string; programId: string }) {
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const q = useQuery({
    ...resourceOptions<Page<Row>>(
      `/v1/programs/${programId}/memberships?membership_status=active&limit=25&offset=${offset}`,
    ),
    enabled: open,
  });
  return (
    <div>
      <Button size="sm" variant="outline" onClick={() => setOpen(!open)}>
        Selecionar creators
      </Button>
      {open ? (
        <div className="participant-picker panel">
          <h3>Parcerias ativas do programa</h3>
          {q.isPending ? (
            <Loading />
          ) : q.error ? (
            <ErrorState error={q.error} />
          ) : q.data.items.length ? (
            q.data.items.map((r) => (
              <label key={String(r.id)}>
                <input
                  type="checkbox"
                  checked={selected.includes(String(r.id))}
                  onChange={(e) =>
                    setSelected((v) =>
                      e.target.checked ? [...v, String(r.id)] : v.filter((id) => id !== r.id),
                    )
                  }
                />
                {String((r.creator as Row)?.display_name ?? r.id)}
              </label>
            ))
          ) : (
            <Empty />
          )}
          <div className="toolbar-group">
            <Button
              size="sm"
              variant="ghost"
              disabled={!offset}
              onClick={() => setOffset(offset - 25)}
            >
              Anterior
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={!q.data || offset + 25 >= q.data.total}
              onClick={() => setOffset(offset + 25)}
            >
              Próxima
            </Button>
            <ActionButton
              action={{
                title: `Confirmar seleção (${selected.length})`,
                path: `/v1/campaigns/${campaignId}/participants`,
                contract: '/v1/campaigns/{campaign_id}/participants',
                initial: { membership_ids: selected },
                hidden: ['membership_ids'],
                disabled: !selected.length || selected.length > 100,
                success: () => {
                  setSelected([]);
                  setOpen(false);
                },
              }}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
