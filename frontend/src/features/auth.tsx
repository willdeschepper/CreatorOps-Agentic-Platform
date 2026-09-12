import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from '@tanstack/react-router';
import { ArrowUpRight, Leaf } from 'lucide-react';
import { bodySchema } from '../api/contract';
import {
  ApiError,
  queryClient,
  request,
  resourceOptions,
  tokenStore,
  type Schema,
} from '../api/client';
import { ActionButton, ContractForm } from '../components/form';
import { Empty, ErrorState, Loading, RecordDetails } from '../components/data';
import { Button } from '../components/ui/button';
function loginError(error: unknown): unknown {
  if (!(error instanceof ApiError) || error.status !== 401) return error;
  const message =
    error.message === 'Staff login requires brand_slug'
      ? 'Esta conta usa o acesso Equipe da marca. Selecione essa opção e confira a marca.'
      : error.message === 'User does not belong to this brand'
        ? 'Esta conta não pertence à marca informada. Confira a marca e tente novamente.'
        : error.message === 'User is inactive'
          ? 'Esta conta está inativa. Fale com a equipe responsável.'
          : error.message === 'Invalid credentials'
            ? 'E-mail ou senha inválidos. Confira os dados e tente novamente.'
            : 'Não foi possível confirmar esta conta. Tente entrar novamente.';
  return new ApiError(error.status, error.code, message, error.requestId, error.fields);
}
export function AuthPage({ register = false }: { register?: boolean }) {
  const [creator, setCreator] = useState(false);
  const navigate = useNavigate();
  const [registered, setRegistered] = useState(false);
  const mutation = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      if (register) {
        await request('/v1/auth/register', { method: 'POST', body: JSON.stringify(body) });
        setRegistered(true);
        return;
      }
      const token = await request<Schema<'TokenResponse'>>('/v1/auth/token', {
        method: 'POST',
        body: JSON.stringify({ ...body, brand_slug: creator ? null : body.brand_slug }),
      });
      await queryClient.cancelQueries();
      queryClient.clear();
      tokenStore.set(token.access_token);
      await request('/v1/auth/me');
      void navigate({ to: '/app' });
    },
  });
  const authError = loginError(mutation.error);
  return (
    <div className="auth-layout">
      <aside className="auth-story">
        <Link to="/login" className="wordmark">
          <span className="logo-mark">
            <Leaf size={20} />
          </span>
          creatorops<span className="wordmark-dot">.</span>
        </Link>
        <div>
          <p className="eyebrow">CRIAR É UMA RELAÇÃO.</p>
          <h1>
            O cuidado por trás
            <br />
            de cada resultado.
          </h1>
          <p>
            Da primeira parceria ao próximo pagamento.
            <br />
            Uma operação clara, do começo ao fim.
          </p>
          <div className="auth-art" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </div>
        <small>OPERAÇÃO LOCAL · CONEXÕES REAIS NO SEU WORKSPACE</small>
      </aside>
      <main className="auth-form-wrap">
        <div className="auth-form">
          <span className="eyebrow">BEM-VINDO AO CREATOROPS</span>
          <h2>{register ? 'Seu próximo capítulo.' : 'Que bom ter você aqui.'}</h2>
          <p className="muted">
            {register
              ? 'Crie seu perfil para começar uma parceria.'
              : 'Entre para acompanhar o que estamos criando.'}
          </p>
          {registered ? (
            <>
              <div role="status" className="success-message">
                Perfil criado. Entre com seu e-mail e senha na opção Creator.
              </div>
              <Button asChild>
                <Link to="/login">Ir para o login</Link>
              </Button>
            </>
          ) : (
            <>
              {!register ? (
                <div className="segmented" aria-label="Tipo de acesso">
                  <button
                    type="button"
                    aria-pressed={!creator}
                    onClick={() => {
                      mutation.reset();
                      setCreator(false);
                    }}
                  >
                    Equipe da marca
                  </button>
                  <button
                    type="button"
                    aria-pressed={creator}
                    onClick={() => {
                      mutation.reset();
                      setCreator(true);
                    }}
                  >
                    Creator
                  </button>
                </div>
              ) : null}
              <ContractForm
                schema={bodySchema(register ? '/v1/auth/register' : '/v1/auth/token')}
                initial={register ? {} : { brand_slug: 'creatorops-demo' }}
                hidden={creator ? ['brand_slug'] : []}
                onSubmit={(data) => mutation.mutate(data)}
                pending={mutation.isPending}
                error={authError}
                errorTitle={
                  register ? 'Não foi possível criar o perfil' : 'Não foi possível entrar'
                }
                errorRetry={false}
                submitLabel={register ? 'Criar meu perfil' : 'Entrar no workspace'}
              />
            </>
          )}
          <p className="auth-switch">
            {register ? 'Já tem uma conta?' : 'Quer criar com a gente?'}{' '}
            <Link to={register ? '/login' : '/register'}>
              {register ? 'Entrar' : 'Cadastre-se'} <ArrowUpRight size={14} />
            </Link>
          </p>
          <div className="auth-footnote">
            <span className="live-dot" />
            Ambiente local · seus dados ficam nesta operação
          </div>
        </div>
      </main>
    </div>
  );
}
export function InvitePage() {
  const { token } = useParams({ strict: false }) as { token: string };
  const q = useQuery(
    resourceOptions<Schema<'InvitationInspectResponse'>>(
      `/v1/invitations/${encodeURIComponent(token)}`,
    ),
  );
  const logged = !!tokenStore.get();
  const me = useQuery({ ...resourceOptions<Schema<'MeResponse'>>('/v1/auth/me'), enabled: logged });
  return (
    <main className="invite-page">
      <Link to="/login" className="wordmark">
        creatorops.
      </Link>
      <div className="panel detail-panel">
        <h1>Uma nova parceria começa aqui.</h1>
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorState error={q.error} />
        ) : (
          <>
            <RecordDetails data={q.data} />
            {q.data.status !== 'pending' ? (
              <Empty title="Este convite não está disponível">
                Confira o estado e a validade acima.
              </Empty>
            ) : me.data?.kind === 'creator' ? (
              <ActionButton
                action={{
                  title: 'Aceitar convite',
                  path: `/v1/invitations/${encodeURIComponent(token)}/accept`,
                  contract: '/v1/invitations/{token}/accept',
                  description:
                    'O e-mail da sua conta precisa corresponder ao convite. Após o aceite, leia e aceite os termos na sua parceria.',
                }}
              />
            ) : (
              <p>
                Entre com uma conta de creator e volte a este link para aceitar o convite.{' '}
                <Link to="/login">Entrar</Link> · <Link to="/register">Criar perfil</Link>
              </p>
            )}
          </>
        )}
      </div>
    </main>
  );
}
