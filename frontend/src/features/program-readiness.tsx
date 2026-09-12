import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { AlertCircle, Check } from 'lucide-react';
import { request, type Page } from '../api/client';
import type { Role } from '../app/session';
import { financiers, operators } from '../app/session';
import { ActionButton } from '../components/form';
import { ErrorState, type Row } from '../components/data';

type Readiness = { terms: boolean; defaultPlan: boolean };

async function hasMatchingRow(
  path: string,
  matches: (row: Row) => boolean,
  signal: AbortSignal,
): Promise<boolean> {
  let offset = 0;
  while (true) {
    const page = await request<Page<Row>>(`${path}?limit=100&offset=${offset}`, { signal });
    if (page.items.some(matches)) return true;
    offset += page.items.length;
    if (!page.items.length || offset >= page.total) return false;
  }
}

export function useProgramReadiness(programId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['api', 'program-readiness', programId],
    enabled,
    queryFn: async ({ signal }): Promise<Readiness> => {
      const base = `/v1/programs/${encodeURIComponent(programId)}`;
      const [terms, defaultPlan] = await Promise.all([
        hasMatchingRow(`${base}/terms`, (row) => row.required === true, signal),
        hasMatchingRow(`${base}/commission-plans`, (row) => row.campaign_id == null, signal),
      ]);
      return { terms, defaultPlan };
    },
  });
}

export function ProgramReadiness({
  programId,
  role,
  result,
}: {
  programId: string;
  role: Role;
  result: UseQueryResult<Readiness>;
}) {
  const terms = result.data?.terms;
  const defaultPlan = result.data?.defaultPlan;
  const ready = terms && defaultPlan;
  const canPublish = operators.includes(role);
  const canCreatePlan = financiers.includes(role);
  return (
    <section className="program-readiness panel" aria-label="Preparação do programa">
      <div className="program-readiness-heading">
        <div>
          <p className="eyebrow">ANTES DE ATIVAR</p>
          <h2>{ready ? 'Programa pronto para ativação' : 'O que falta para ativar'}</h2>
          <p>O servidor exige termos obrigatórios publicados e um plano padrão sem campanha.</p>
        </div>
        {ready ? <span className="readiness-ready">Pronto</span> : null}
      </div>
      {result.isPending ? (
        <p role="status" className="muted">
          Verificando termos e planos na API local…
        </p>
      ) : result.error ? (
        <ErrorState error={result.error} retry={() => void result.refetch()} />
      ) : (
        <div className="readiness-steps" aria-live="polite">
          <div className={`readiness-step ${terms ? 'is-complete' : ''}`}>
            <span className="readiness-icon" aria-hidden="true">
              {terms ? <Check size={17} /> : <AlertCircle size={17} />}
            </span>
            <div>
              <strong>Termos obrigatórios publicados</strong>
              <p>
                {terms
                  ? 'Concluído. Não é necessário ativar os termos novamente.'
                  : canPublish
                    ? 'Publique uma versão obrigatória dos termos.'
                    : 'Peça a owner ou ops para publicar uma versão obrigatória.'}
              </p>
            </div>
            {!terms && canPublish ? (
              <ActionButton
                action={{
                  title: 'Publicar termos obrigatórios',
                  path: `/v1/programs/${programId}/terms`,
                  contract: '/v1/programs/{program_id}/terms',
                  initial: { required: true },
                  hidden: ['required'],
                }}
              />
            ) : null}
          </div>
          <div className={`readiness-step ${defaultPlan ? 'is-complete' : ''}`}>
            <span className="readiness-icon" aria-hidden="true">
              {defaultPlan ? <Check size={17} /> : <AlertCircle size={17} />}
            </span>
            <div>
              <strong>Plano padrão do programa</strong>
              <p>
                {defaultPlan
                  ? 'Concluído. Existe um plano sem campanha vinculada.'
                  : canCreatePlan
                    ? 'Crie um plano sem campanha. Planos de campanha não substituem o padrão.'
                    : 'Peça a owner ou finance para criar um plano sem campanha.'}
              </p>
            </div>
            {!defaultPlan && canCreatePlan ? (
              <ActionButton
                action={{
                  title: 'Criar plano padrão',
                  path: `/v1/programs/${programId}/commission-plans`,
                  contract: '/v1/programs/{program_id}/commission-plans',
                  initial: { campaign_id: null },
                  hidden: ['campaign_id'],
                  description:
                    'Este plano vale para o programa sem campanha. Informe taxa, vigência e demais regras; confirme antes de ativar o programa.',
                }}
              />
            ) : null}
          </div>
        </div>
      )}
    </section>
  );
}
