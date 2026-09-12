import { useSearchState } from '../app/search';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useNavigate } from '@tanstack/react-router';
import { ArrowUpRight, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';
import { resourceOptions, type Page } from '../api/client';
import { type Role } from '../app/session';
import { Button } from '../components/ui/button';
import {
  Empty,
  ErrorState,
  Heading,
  Loading,
  RecordDetails,
  Value,
  type Row,
} from '../components/data';
import { label } from '../lib/format';
export function ContextPicker({
  creator = false,
  name = 'context',
  onSelect,
  value,
}: {
  creator?: boolean;
  name?: string;
  onSelect?: (id: string) => void;
  value?: string;
}) {
  const { search, update } = useSearchState();
  const offset = Math.max(0, Number(search[`${name}_offset`]) || 0);
  const q = useQuery(
    resourceOptions<Page<Row>>(
      `/v1/${creator ? 'memberships/me' : 'programs'}?limit=25&offset=${offset}`,
    ),
  );
  const current = value ?? String(search[name] ?? '');
  const set = (id: string) => (onSelect ? onSelect(id) : update({ [name]: id }));
  return (
    <div className="context-picker">
      <label>
        {creator ? 'Parceria' : 'Programa'}
        <select
          aria-label={creator ? 'Selecionar parceria' : 'Selecionar programa'}
          value={current}
          onChange={(e) => set(e.target.value)}
        >
          <option value="">Selecione {creator ? 'uma parceria' : 'um programa'}</option>
          {current && !q.data?.items.some((r) => r.id === current) ? (
            <option value={current}>{current}</option>
          ) : null}
          {q.data?.items.map((row) => (
            <option key={String(row.id)} value={String(row.id)}>
              {String(row.name ?? row.program_name ?? row.id)}
            </option>
          ))}
        </select>
      </label>
      {q.error ? <ErrorState error={q.error} retry={() => void q.refetch()} /> : null}
      {q.data && q.data.total > 25 ? (
        <>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Programas anteriores"
            disabled={!offset}
            onClick={() => update({ [`${name}_offset`]: Math.max(0, offset - 25) })}
          >
            <ChevronLeft size={16} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Próximos programas"
            disabled={offset + 25 >= q.data.total}
            onClick={() => update({ [`${name}_offset`]: offset + 25 })}
          >
            <ChevronRight size={16} />
          </Button>
        </>
      ) : null}
    </div>
  );
}
export function Report({ endpoint }: { endpoint: string }) {
  const q = useQuery(resourceOptions<Row>(endpoint));
  if (q.isPending) return <Loading />;
  if (q.error) return <ErrorState error={q.error} retry={() => void q.refetch()} />;
  const data = q.data;
  const primary = [
    'net_gmv',
    'orders',
    data.active_creators !== undefined
      ? 'active_creators'
      : data.selected_creators !== undefined
        ? 'selected_creators'
        : 'approved_posts',
    data.commission_available !== undefined ? 'commission_available' : 'net_commission',
  ];
  return (
    <>
      <div className="metrics-grid">
        {primary.map((key, i) => (
          <article className={`metric metric-${i}`} key={key}>
            <p>{label(key)}</p>
            <strong>
              <Value name={key} value={data[key]} />
            </strong>
            <span>
              {
                [
                  'Após devoluções',
                  'No escopo selecionado',
                  'Conexões que geram resultado',
                  'No escopo selecionado',
                ][i]
              }
            </span>
          </article>
        ))}
      </div>
      <div className="report-grid">
        <section className="panel report-panel">
          <div className="section-heading">
            <h2>O resultado, em detalhes</h2>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Atualizar relatório"
              onClick={() => void q.refetch()}
            >
              <RefreshCw size={16} />
            </Button>
          </div>
          <RecordDetails
            data={data}
            omit={[
              ...primary,
              'program_id',
              'membership_id',
              'campaign_id',
              'payouts',
              'social_metrics',
            ]}
          />
        </section>
        <div className="report-side">
          <section className="panel report-panel">
            <h2>Conteúdo e alcance</h2>
            <RecordDetails data={(data.social_metrics ?? {}) as Row} />
            {!Object.keys((data.social_metrics as Row) ?? {}).length ? (
              <p className="muted">As métricas aparecem após a importação local.</p>
            ) : null}
          </section>
          {data.payouts ? (
            <section className="panel report-panel">
              <h2>Pagamentos por estado</h2>
              <RecordDetails data={data.payouts as Row} />
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
}
export function Overview({ role, reports = false }: { role: Role; reports?: boolean }) {
  const search = useLocation().search as Record<string, string>;
  const creator = role === 'creator';
  const id = search.context;
  return (
    <>
      <Heading
        eyebrow={reports ? 'MENSURAÇÃO / RESULTADOS' : 'SEU WORKSPACE, EM PERSPECTIVA'}
        title={reports ? 'Resultados' : 'Cada parceria, um próximo passo.'}
        description={
          reports
            ? 'Resultados reais, no contexto certo.'
            : 'Uma visão clara de quem cria, do que acontece e do que vem a seguir.'
        }
      >
        <ContextPicker creator={creator} />
      </Heading>
      {id ? (
        <Report
          endpoint={`/v1/reports/${creator ? 'memberships' : 'programs'}/${encodeURIComponent(id)}/overview`}
        />
      ) : (
        <section className="overview-intro">
          <div>
            <span className="eyebrow">DO PRIMEIRO ACEITE AO RESULTADO</span>
            <h2>
              Boas relações.
              <br />
              Operação bem cuidada.
            </h2>
            <p>
              Escolha {creator ? 'uma parceria' : 'um programa'} acima para acompanhar os resultados
              e encontrar o próximo passo.
            </p>
            <Button asChild>
              <Link to={creator ? '/app/memberships' : '/app/programs'}>
                Explorar {creator ? 'parcerias' : 'programas'} <ArrowUpRight size={16} />
              </Link>
            </Button>
          </div>
          <div className="orbit-art" aria-hidden="true">
            <div className="orbit orbit-a" />
            <div className="orbit orbit-b" />
            <div className="orbit orbit-c" />
            <div className="orbit-core">
              c<span>o</span>
            </div>
            <span className="orbit-note note-a">RELAÇÕES</span>
            <span className="orbit-note note-b">RESULTADOS</span>
          </div>
        </section>
      )}
      <section className="journey-strip" aria-label="Etapas da operação">
        {['Programa', 'Parceria', 'Conteúdo & vendas', 'Comissão', 'Pagamento'].map((name, i) => (
          <div key={name}>
            <span>0{i + 1}</span>
            <strong>{name}</strong>
          </div>
        ))}
      </section>
      <div className="quick-links">
        <Link to="/app/programs">
          <span>01 / ORGANIZAR</span>
          <h3>Programas e regras</h3>
          <p>Termos, campanhas e o começo de cada relação.</p>
          <ArrowUpRight />
        </Link>
        {role === 'creator' || role === 'ops' || role === 'owner' ? (
          <Link to={creator ? '/app/memberships' : '/app/applications'}>
            <span>02 / CONECTAR</span>
            <h3>{creator ? 'Minhas parcerias' : 'Próximas parcerias'}</h3>
            <p>O aceite certo abre caminho para criar.</p>
            <ArrowUpRight />
          </Link>
        ) : (
          <Link to="/app/finance/reconciliation">
            <span>02 / CONFERIR</span>
            <h3>Reconciliação</h3>
            <p>Evidências antes de qualquer correção.</p>
            <ArrowUpRight />
          </Link>
        )}
      </div>
    </>
  );
}
