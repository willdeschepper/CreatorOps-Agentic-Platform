import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { money } from '../src/lib/format';
import { bodySchema, normalize, validator } from '../src/api/contract';
import { detailActions } from '../src/features/actions';
import { ApiError } from '../src/api/client';
import { ErrorState, Status } from '../src/components/data';
import { pageNumber } from '../src/components/collection';
describe('integridade financeira na interface', () => {
  it('preserva precisão e sinais sem aritmética em ponto flutuante', () => {
    expect(money('999999999999.99')).toBe('R$ 999.999.999.999,99');
    expect(money('-0.01')).toBe('−R$ 0,01');
    expect(money('0.00')).toBe('R$ 0,00');
  });
  it('não oferece execução para proposta sem aprovação ou desatualizada', () => {
    for (const state of ['draft', 'gated', 'blocked', 'rejected', 'stale', 'executed'])
      expect(
        detailActions('proposals', { id: 'p', state, approved_by: 'human' }, 'finance').some(
          (a) => a.title === 'Executar correção',
        ),
      ).toBe(false);
    expect(
      detailActions('proposals', { id: 'p', state: 'approved', approved_by: null }, 'finance').some(
        (a) => a.title === 'Executar correção',
      ),
    ).toBe(false);
    expect(
      detailActions(
        'proposals',
        { id: 'p', state: 'approved', approved_by: 'human' },
        'finance',
      ).some((a) => a.title === 'Executar correção'),
    ).toBe(true);
  });
  it('aprovação e execução nunca aparecem como a mesma ação', () => {
    const actions = detailActions('proposals', { id: 'p', state: 'gated' }, 'owner');
    expect(actions.some((a) => a.title === 'Aprovar proposta')).toBe(true);
    expect(actions.some((a) => a.title === 'Executar correção')).toBe(false);
  });
  it('owner/finance aprovam lotes apenas draft; ops não aprova', () => {
    expect(detailActions('payout-batches', { id: 'b', status: 'unknown' }, 'finance')).toEqual([]);
    expect(detailActions('payout-batches', { id: 'b', status: 'draft' }, 'ops')).toEqual([]);
  });
});
describe('contrato e feedback', () => {
  it('valida comentário obrigatório com o contrato real', () => {
    const s = bodySchema('/v1/agent/proposals/{proposal_id}/approve');
    expect(validator(s).safeParse({ comment: 'ok' }).success).toBe(false);
    expect(validator(s).safeParse({ comment: 'Evidências conferidas' }).success).toBe(true);
  });
  it('normaliza inteiros e mantém dinheiro string', () => {
    const s = bodySchema('/v1/programs');
    const value = normalize(
      {
        name: 'Programa',
        slug: 'programa',
        attribution_window_days: '30',
        return_window_days: '7',
        payout_minimum: '100.01',
      },
      s,
    );
    expect(value).toMatchObject({ payout_minimum: '100.01', return_window_days: 7 });
    expect(validator(s).safeParse(value).success).toBe(true);
  });
  it('limita paginação e não usa tamanho de página como total', () => {
    expect(pageNumber(-5, 0, 0, 100)).toBe(0);
    expect(pageNumber(500, 25, 1, 100)).toBe(25);
  });
  it('explica conflitos e mostra request ID disponível', () => {
    render(
      <ErrorState
        error={new ApiError(409, 'stale', 'O estado mudou.', 'req-local')}
        retry={() => {}}
      />,
    );
    expect(screen.getByRole('alert')).toHaveTextContent('O estado mudou.');
    expect(screen.getByRole('button', { name: 'Recarregar estado' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Copiar req-local' })).toBeVisible();
  });
  it('explica a pré-condição de ativação na linguagem da interface', () => {
    render(
      <ErrorState
        error={
          new ApiError(
            409,
            'program_not_ready',
            'An active program requires published terms and a default commission plan',
          )
        }
      />,
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Programa ainda não pode ser ativado');
    expect(screen.getByRole('alert')).toHaveTextContent('plano padrão sem campanha');
  });
  it('não depende apenas de cor para resultado desconhecido', () => {
    render(<Status value="unknown" />);
    expect(screen.getByText('Resultado desconhecido')).toBeVisible();
    expect(screen.getByText('unknown')).toBeVisible();
  });
});
