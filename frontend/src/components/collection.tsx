import { useSearchState } from '../app/search';
import { useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLocation, useNavigate } from '@tanstack/react-router';
import { ChevronLeft, ChevronRight, RefreshCw, SlidersHorizontal } from 'lucide-react';
import { resourceOptions, type Page } from '../api/client';
import { displaySchema, operation } from '../api/contract';
import { label } from '../lib/format';
import type { Collection } from '../features/catalog';
import { Button } from './ui/button';
import { DataTable, Empty, ErrorState, Loading, type Row } from './data';
export function pageNumber(v: unknown, fallback: number, min: number, max: number) {
  const n = Number(v);
  return Number.isSafeInteger(n) && n >= min && n <= max ? n : fallback;
}
export function CollectionView({
  config,
  scope = '',
  actions,
  hideFilters = [],
  rowActions,
}: {
  config: Collection;
  scope?: string;
  actions?: ReactNode;
  hideFilters?: string[];
  rowActions?: (row: Row) => ReactNode;
}) {
  const { search, update } = useSearchState();
  const [poll, setPoll] = useState(false);
  const [pollStarted, setPollStarted] = useState(0);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const name = (key: string) => (scope ? `${scope}_${key}` : key);
  const limit = pageNumber(search[name('limit')], 25, 1, 100);
  const offset = pageNumber(search[name('offset')], 0, 0, Number.MAX_SAFE_INTEGER);
  const params = (operation(config.contract)?.parameters ?? []).filter(
    (p) => p.in === 'query' && !['limit', 'offset', ...hideFilters].includes(p.name),
  );
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  for (const p of params) {
    const v = search[name(p.name)];
    if (v) query.set(p.name, String(v));
  }
  const url = `${config.endpoint}${config.endpoint.includes('?') ? '&' : '?'}${query}`;
  const result = useQuery({
    ...resourceOptions<Page<Row>>(url),
    refetchInterval: (query) => {
      if (!poll || Date.now() - pollStarted > 60_000) return false;
      if (config.contract === '/v1/posts') return 3000;
      return query.state.data?.items.some((row) =>
        ['pending', 'processing', 'running'].includes(String(row.status)),
      )
        ? 3000
        : false;
    },
    refetchIntervalInBackground: false,
  });
  const change = (key: string, value: string | number) => {
    update({
      [name(key)]: value || undefined,
      ...(key !== 'offset' ? { [name('offset')]: 0 } : {}),
    });
  };
  return (
    <section className="collection panel">
      <div className="collection-toolbar">
        <div className="toolbar-group">
          <strong>{config.title}</strong>
          {result.data ? <span className="count">{result.data.total}</span> : null}
        </div>
        <div className="toolbar-group">
          {actions}
          {params.length ? (
            <Button
              variant="ghost"
              size="sm"
              aria-expanded={filtersOpen}
              onClick={() => setFiltersOpen(!filtersOpen)}
            >
              <SlidersHorizontal size={15} />
              Filtros
            </Button>
          ) : null}
          {config.poll ? (
            <label className="poll-toggle">
              <input
                type="checkbox"
                checked={poll}
                onChange={(e) => {
                  setPoll(e.target.checked);
                  setPollStarted(Date.now());
                }}
              />
              Acompanhar por até 1 min
            </label>
          ) : null}
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Atualizar ${config.title}`}
            disabled={result.isFetching}
            onClick={() => void result.refetch()}
          >
            <RefreshCw size={16} className={result.isFetching ? 'spin' : ''} />
          </Button>
        </div>
      </div>
      {filtersOpen ? (
        <form className="filters" onSubmit={(e) => e.preventDefault()}>
          {params.map((p) => {
            const s = displaySchema(p.schema);
            return (
              <label key={p.name}>
                {label(
                  p.name.replace(
                    /^(application|membership|participant|content|order|commission|program|campaign|batch|payout|run|invitation|proposal|finding)_status$/,
                    'status',
                  ),
                )}
                {s.enum ? (
                  <select
                    value={String(search[name(p.name)] ?? '')}
                    onChange={(e) => change(p.name, e.target.value)}
                  >
                    <option value="">Todos</option>
                    {s.enum.map((v) => (
                      <option key={v} value={v}>
                        {label(v)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    value={String(search[name(p.name)] ?? '')}
                    placeholder={s.format === 'date-time' ? '2026-09-12T00:00:00-03:00' : undefined}
                    onChange={(e) => change(p.name, e.target.value)}
                  />
                )}
              </label>
            );
          })}
        </form>
      ) : null}
      {result.isPending ? (
        <Loading />
      ) : result.error ? (
        <ErrorState error={result.error} retry={() => void result.refetch()} />
      ) : result.data.items.length ? (
        <DataTable
          items={result.data.items}
          columns={config.columns}
          columnLabels={config.columnLabels}
          renderCell={config.renderCell}
          href={
            config.detail
              ? (row) => `/app/${config.detail}/${row.id}`
              : config.contract === '/v1/payouts'
                ? (row) => `/app/finance/payout-batches/${row.batch_id}`
                : undefined
          }
          actions={rowActions}
        />
      ) : (
        <Empty />
      )}
      <footer className="pagination">
        <span>
          {result.data?.total
            ? `${offset + 1}–${Math.min(offset + limit, result.data.total)} de ${result.data.total}`
            : '0 registros'}
        </span>
        <div className="toolbar-group">
          <label>
            Por página{' '}
            <select
              aria-label="Registros por página"
              value={limit}
              onChange={(e) => change('limit', Number(e.target.value))}
            >
              {[25, 50, 100].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </label>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Página anterior"
            disabled={offset === 0}
            onClick={() => change('offset', Math.max(0, offset - limit))}
          >
            <ChevronLeft size={17} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Próxima página"
            disabled={!result.data || offset + limit >= result.data.total}
            onClick={() => change('offset', offset + limit)}
          >
            <ChevronRight size={17} />
          </Button>
        </div>
      </footer>
    </section>
  );
}
