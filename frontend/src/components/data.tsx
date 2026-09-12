import { useState, type ReactNode } from 'react';
import {
  AlertCircle,
  ArrowUpRight,
  Check,
  Copy,
  Inbox,
  LoaderCircle,
  RefreshCw,
} from 'lucide-react';
import { Link } from '@tanstack/react-router';
import { ApiError, API } from '../api/client';
import { date, financialFields, label, money, timezone } from '../lib/format';
import { Button } from './ui/button';
export type Row = Record<string, unknown>;
export function Status({ value }: { value: string }) {
  return (
    <span className={`status status-${value}`}>
      <span className="status-dot" />
      {label(value)}
      <small>{value}</small>
    </span>
  );
}
export function Copyable({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="copyable"
      title={value}
      onClick={() => {
        void navigator.clipboard
          .writeText(value)
          .then(() => setCopied(true))
          .catch(() => setCopied(false));
      }}
      aria-label={`Copiar ${value}`}
    >
      <span>{value}</span>
      {copied ? <Check size={12} /> : <Copy size={12} />}
    </button>
  );
}
export function ErrorState({
  error,
  retry,
  title,
}: {
  error: unknown;
  retry?: () => void;
  title?: string;
}) {
  const e = error instanceof ApiError ? error : null;
  const programNotReady = e?.code === 'program_not_ready';
  return (
    <div className="notice error" role="alert">
      <AlertCircle size={20} />
      <div>
        <strong>
          {title ??
            (programNotReady
              ? 'Programa ainda não pode ser ativado'
              : e?.status === 403
                ? 'Acesso não permitido'
                : e?.status === 404
                  ? 'Registro não encontrado'
                  : e?.status === 409
                    ? 'O estado mudou'
                    : e?.status === 401
                      ? 'Sessão expirada'
                      : 'Não foi possível continuar')}
        </strong>
        <p>
          {programNotReady
            ? 'Publique termos obrigatórios e crie um plano padrão sem campanha antes de ativar.'
            : error instanceof Error
              ? error.message
              : 'Verifique a conexão com a API local.'}
        </p>
        {e?.fields?.map((f, i) => (
          <p key={i}>
            {f.loc
              .map(String)
              .filter((v) => v !== 'body')
              .map(label)
              .join(' › ')}
            : {f.msg}
          </p>
        ))}
        {e?.requestId ? (
          <small>
            Solicitação: <Copyable value={e.requestId} />
          </small>
        ) : null}
        {retry ? (
          <Button variant="outline" size="sm" onClick={retry}>
            <RefreshCw size={14} />
            Recarregar estado
          </Button>
        ) : null}
      </div>
    </div>
  );
}
export function Loading() {
  return (
    <div className="empty" role="status">
      <LoaderCircle className="spin" size={24} />
      <p>Carregando dados locais…</p>
    </div>
  );
}
export function Empty({
  title = 'Nenhum registro por aqui',
  children,
}: {
  title?: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <Inbox size={28} />
      <h3>{title}</h3>
      <p>{children ?? 'Ajuste os filtros ou inicie a próxima etapa da operação.'}</p>
    </div>
  );
}
export function Heading({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow ?? 'CREATOROPS / WORKSPACE'}</p>
        <h1>{title}</h1>
        {description ? <p className="lead">{description}</p> : null}
      </div>
      <div className="heading-actions">{children}</div>
    </header>
  );
}
export function Notice({ children }: { children: ReactNode }) {
  return (
    <div className="notice">
      <AlertCircle size={18} />
      <div>{children}</div>
    </div>
  );
}
export function Value({ name, value }: { name: string; value: unknown }) {
  if (value === null || value === undefined || value === '')
    return <span className="muted">—</span>;
  if (typeof value === 'boolean') return <span>{value ? 'Sim' : 'Não'}</span>;
  if (name === 'gates' && Array.isArray(value))
    return (
      <div className="gate-list">
        {value.length ? (
          value.map((run: Row) => (
            <section className="gate-run" key={String(run.id)}>
              <div className="section-heading">
                <strong>Validação de {date(String(run.created_at))}</strong>
                <Status value={String(run.result)} />
              </div>
              {(run.checks as Row[]).map((check, i) => (
                <div className="gate-check" key={i}>
                  <span className={check.passed ? 'gate-pass' : 'gate-fail'}>
                    {check.passed ? <Check size={17} /> : <AlertCircle size={17} />}
                  </span>
                  <div>
                    <strong>{label(String(check.name))}</strong>
                    <small>{String(check.name)}</small>
                    <p>{String(check.detail)}</p>
                  </div>
                  <span>{check.passed ? 'Passou' : 'Bloqueado'}</span>
                </div>
              ))}
            </section>
          ))
        ) : (
          <span className="muted">
            Execute os gates para avaliar as evidências antes da aprovação.
          </span>
        )}
      </div>
    );
  if (name === 'assets' && Array.isArray(value))
    return (
      <div className="asset-grid">
        {value.length ? (
          value.map((asset: Row) => (
            <article className="asset-card" key={String(asset.id)}>
              <strong>{asset.asset_type === 'coupon' ? 'Cupom' : 'Link de afiliado'}</strong>
              <span className={`status ${asset.active ? 'status-active' : ''}`}>
                <span className="status-dot" />
                {asset.active ? 'Ativo' : 'Inativo'}
                <small>active={String(asset.active)}</small>
              </span>
              <Copyable
                value={asset.asset_type === 'link' ? `${API}/r/${asset.code}` : String(asset.code)}
              />
              <small>{asset.campaign_id ? 'Asset de campanha' : 'Asset do programa'}</small>
            </article>
          ))
        ) : (
          <span className="muted">Assets disponíveis após o aceite dos termos vigentes.</span>
        )}
      </div>
    );
  if (typeof value === 'object')
    return Array.isArray(value) ? (
      <div className="nested-list">
        {value.length ? (
          value.map((v, i) => (
            <div className="nested-item" key={i}>
              {typeof v === 'object' && v !== null ? (
                <RecordDetails data={v as Row} />
              ) : (
                <Value name={name} value={v} />
              )}
            </div>
          ))
        ) : (
          <span className="muted">Nenhum registro</span>
        )}
      </div>
    ) : (
      <RecordDetails data={value as Row} />
    );
  const text = String(value);
  if (
    ['action', 'kind', 'reason', 'entry_type', 'finding_type'].includes(name) &&
    label(text) !== text.replaceAll('_', ' ')
  )
    return (
      <span>
        {label(text)} <small className="muted">{text}</small>
      </span>
    );
  if (['status', 'state', 'bucket', 'result'].includes(name)) return <Status value={text} />;
  if (financialFields.has(name) && typeof value === 'string')
    return <span className="money">{money(text)}</span>;
  if (name.endsWith('_at') || name === 'active_from')
    return (
      <time dateTime={text} title={timezone}>
        {date(text)}
      </time>
    );
  if (
    name === 'id' ||
    name.endsWith('_id') ||
    name.endsWith('_hash') ||
    name === 'code' ||
    name === 'idempotency_key'
  )
    return <Copyable value={text} />;
  return <span className="value-text">{text}</span>;
}
export function RecordDetails({ data, omit = [] }: { data: Row; omit?: string[] }) {
  return (
    <dl className="record-details">
      {Object.entries(data)
        .filter(([key]) => !omit.includes(key) && key !== 'brand_id' && key !== 'firestore_path')
        .map(([key, value]) => (
          <div
            key={key}
            className={typeof value === 'object' && value !== null ? 'detail-wide' : ''}
          >
            <dt>{label(key)}</dt>
            <dd>
              <Value name={key} value={value} />
            </dd>
          </div>
        ))}
    </dl>
  );
}
export function DataTable({
  items,
  columns,
  href,
  actions,
  columnLabels,
  renderCell,
}: {
  items: Row[];
  columns: string[];
  href?: (row: Row) => string;
  actions?: (row: Row) => ReactNode;
  columnLabels?: Record<string, string>;
  renderCell?: (row: Row, column: string) => ReactNode | undefined;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{columnLabels?.[c] ?? label(c)}</th>
            ))}
            {href || actions ? (
              <th>
                <span className="sr-only">Ações</span>
              </th>
            ) : null}
          </tr>
        </thead>
        <tbody>
          {items.map((row, i) => (
            <tr key={String(row.id ?? i)}>
              {columns.map((c, index) => (
                <td key={c}>
                  {index === 0 && href ? (
                    <Link className="row-link" to={href(row)}>
                      {String(row[c] ?? row.id)}
                    </Link>
                  ) : (
                    (renderCell?.(row, c) ?? <Value name={c} value={row[c]} />)
                  )}
                </td>
              ))}
              {href || actions ? (
                <td className="row-actions">
                  {actions?.(row)}
                  {href ? (
                    <Link
                      className="icon-link"
                      aria-label={`Abrir ${String(row.name ?? row.id)}`}
                      to={href(row)}
                    >
                      <ArrowUpRight size={18} />
                    </Link>
                  ) : null}
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
