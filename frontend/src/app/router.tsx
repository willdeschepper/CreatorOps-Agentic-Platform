import {
  createRootRoute,
  createRoute,
  createRouter,
  Link,
  Outlet,
  useLocation,
  useNavigate,
} from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  CircleDollarSign,
  ClipboardList,
  FileCheck2,
  Fingerprint,
  Flower2,
  LayoutDashboard,
  Leaf,
  LogOut,
  Menu,
  PanelLeftClose,
  ScanLine,
  ShoppingBag,
  Users,
  Wallet,
  X,
} from 'lucide-react';
import { clearSession, ApiError, resourceOptions } from '../api/client';
import { meOptions, requireSession, roleOf, type Role } from './session';
import { AuthPage, InvitePage } from '../features/auth';
import { Overview, ContextPicker } from '../features/reports';
import { collections, ownCollection } from '../features/catalog';
import { DetailPage } from '../features/details';
import { listActions } from '../features/actions';
import { ActionButton, ActionProvider } from '../components/form';
import { CollectionView } from '../components/collection';
import { Empty, ErrorState, Heading, Loading } from '../components/data';
import { Button } from '../components/ui/button';
import { timezone } from '../lib/format';
const navigation = [
  {
    title: 'Visão geral',
    to: '/app',
    icon: LayoutDashboard,
    roles: ['owner', 'ops', 'finance', 'creator'],
    group: 'WORKSPACE',
  },
  {
    title: 'Programas',
    to: '/app/programs',
    icon: Flower2,
    roles: ['owner', 'ops', 'finance', 'creator'],
  },
  {
    title: 'Candidaturas',
    to: '/app/applications',
    icon: Users,
    roles: ['owner', 'ops', 'creator'],
  },
  {
    title: 'Parcerias',
    to: '/app/memberships',
    icon: BookOpen,
    roles: ['owner', 'ops', 'creator'],
  },
  {
    title: 'Conteúdo',
    to: '/app/posts',
    icon: ScanLine,
    roles: ['owner', 'ops'],
    group: 'MENSURAÇÃO',
  },
  { title: 'Vendas', to: '/app/orders', icon: ShoppingBag, roles: ['owner', 'ops', 'finance'] },
  {
    title: 'Resultados',
    to: '/app/reports',
    icon: Activity,
    roles: ['owner', 'ops', 'finance', 'creator'],
  },
  {
    title: 'Comissões',
    to: '/app/finance/commissions',
    icon: CircleDollarSign,
    roles: ['owner', 'finance'],
    group: 'FINANCEIRO',
  },
  {
    title: 'Lotes de pagamento',
    to: '/app/finance/payout-batches',
    icon: Wallet,
    roles: ['owner', 'finance'],
  },
  {
    title: 'Pagamentos',
    to: '/app/finance/payouts',
    icon: CircleDollarSign,
    roles: ['owner', 'finance'],
  },
  {
    title: 'Histórico financeiro',
    to: '/app/finance/ledger',
    icon: ClipboardList,
    roles: ['owner', 'finance'],
  },
  {
    title: 'Reconciliação',
    to: '/app/finance/reconciliation',
    icon: ScanLine,
    roles: ['owner', 'finance'],
    group: 'CONTROLE AGÊNTICO',
  },
  {
    title: 'Divergências',
    to: '/app/agent/findings',
    icon: Fingerprint,
    roles: ['owner', 'finance'],
  },
  { title: 'Propostas', to: '/app/agent/proposals', icon: FileCheck2, roles: ['owner', 'finance'] },
  { title: 'Auditoria', to: '/app/audit', icon: ClipboardList, roles: ['owner', 'ops', 'finance'] },
];
function Root() {
  return (
    <ActionProvider>
      <Outlet />
    </ActionProvider>
  );
}
function Shell() {
  const me = useQuery(meOptions());
  const [menu, setMenu] = useState(false);
  const navigate = useNavigate();
  const pathname = useLocation({ select: (l) => l.pathname });
  const health = useQuery({
    ...resourceOptions<{ status: string }>('/health/ready'),
    refetchInterval: 30_000,
  });
  useEffect(() => {
    const onLogout = () => void navigate({ to: '/login', replace: true });
    window.addEventListener('creatorops:logout', onLogout);
    return () => window.removeEventListener('creatorops:logout', onLogout);
  }, [navigate]);
  useEffect(() => {
    setMenu(false);
  }, [pathname]);
  if (me.isPending) return <Loading />;
  if (me.error) return <ErrorState error={me.error} />;
  const role = roleOf(me.data);
  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">
        Pular para conteúdo
      </a>
      {menu ? (
        <button className="mobile-scrim" aria-label="Fechar menu" onClick={() => setMenu(false)} />
      ) : null}
      <aside className={`sidebar ${menu ? 'is-open' : ''}`}>
        <Link to="/app" className="wordmark">
          <span className="logo-mark">
            <Leaf size={20} />
          </span>
          creatorops<span className="wordmark-dot">.</span>
        </Link>
        <div className="workspace-card">
          <span className="workspace-avatar">C</span>
          <div>
            <strong>{role === 'creator' ? 'Meu espaço' : 'Creator workspace'}</strong>
            <small>
              {role === 'creator'
                ? 'Creator'
                : role === 'owner'
                  ? 'Administração'
                  : role === 'ops'
                    ? 'Operações'
                    : 'Financeiro'}
            </small>
          </div>
          <PanelLeftClose size={16} />
        </div>
        <nav aria-label="Navegação principal">
          {navigation
            .filter((n) => n.roles.includes(role))
            .map((n) => (
              <div key={n.to}>
                {n.group ? <p className="nav-group">{n.group}</p> : null}
                <Link
                  to={n.to}
                  activeOptions={{ exact: n.to === '/app' }}
                  className={`nav-link ${pathname === n.to || (n.to !== '/app' && pathname.startsWith(n.to + '/')) ? 'active' : ''}`}
                  aria-current={pathname === n.to ? 'page' : undefined}
                >
                  <n.icon size={18} />
                  <span>{n.title}</span>
                  {pathname === n.to ? <span className="nav-active-dot" /> : null}
                </Link>
              </div>
            ))}
        </nav>
        <div className="sidebar-footer">
          <div className="local-note">
            <span className={`live-dot ${health.isError ? 'offline' : ''}`} />
            {health.isError ? 'API indisponível' : 'Ambiente local'}
          </div>
          <button className="user-menu" onClick={() => clearSession()} aria-label="Sair da sessão">
            <span className="user-avatar">{me.data.display_name.slice(0, 2).toUpperCase()}</span>
            <span>
              <strong>{me.data.display_name}</strong>
              <small>{role}</small>
            </span>
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <div className="workspace-main">
        <header className="topbar">
          <div className="toolbar-group">
            <Button
              className="mobile-menu"
              variant="ghost"
              size="icon"
              onClick={() => setMenu(!menu)}
              aria-label="Abrir menu"
              aria-expanded={menu}
            >
              <Menu size={20} />
            </Button>
            <span>Workspace</span>
            <span className="breadcrumb-divider">/</span>
            <strong>{navigation.find((n) => n.to === pathname)?.title ?? 'Detalhe'}</strong>
          </div>
          <div className="topbar-right">
            <span className="local-pill">
              <span className="live-dot" />
              LOCAL
            </span>
            <span className="timezone">{timezone}</span>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <Outlet />
        </main>
        <footer className="workspace-footer">
          <span>CreatorOps · Relações que geram resultado.</span>
          <span>
            Dados da API local <ArrowUpRight size={12} />
          </span>
        </footer>
      </div>
    </div>
  );
}
function Page() {
  const pathname = useLocation({ select: (l) => l.pathname });
  const search = useLocation().search as Record<string, string>;
  const me = useQuery(meOptions());
  if (!me.data) return <Loading />;
  const role = roleOf(me.data);
  const parts = pathname.split('/').filter(Boolean).slice(1);
  if (!parts.length) return <Overview role={role} />;
  const key = parts.at(-1)!;
  if (key === 'reports') return <Overview role={role} reports />;
  if (key === 'memberships') {
    if (!['owner', 'ops', 'creator'].includes(role))
      return (
        <ErrorState
          error={new ApiError(403, 'forbidden', 'Este papel não tem acesso à lista de parcerias.')}
        />
      );
    const creator = role === 'creator';
    const selected = search.context;
    return (
      <>
        <Heading
          title={creator ? 'Minhas parcerias' : 'Parcerias'}
          description="O vínculo entre creator e programa, do aceite dos termos aos resultados."
        >
          {!creator ? <ContextPicker /> : null}
        </Heading>
        {creator || selected ? (
          <CollectionView
            config={{
              title: 'Parcerias',
              description: '',
              roles: [],
              endpoint: creator
                ? '/v1/memberships/me'
                : `/v1/programs/${encodeURIComponent(selected)}/memberships`,
              contract: creator ? '/v1/memberships/me' : '/v1/programs/{program_id}/memberships',
              columns: creator
                ? ['id', 'status', 'activated_at']
                : ['id', 'creator', 'status', 'activated_at'],
              detail: 'memberships',
            }}
          />
        ) : (
          <Empty title="Escolha um programa">As parcerias são organizadas por programa.</Empty>
        )}
      </>
    );
  }
  const isDetail = parts.length > 1 && !['finance', 'agent'].includes(parts.at(-2)!);
  if (isDetail) {
    const kind = parts.at(-2)!;
    const roles =
      collections[kind]?.roles ??
      (kind === 'memberships'
        ? ['owner', 'ops', 'finance', 'creator']
        : ['owner', 'ops', 'finance', 'creator']);
    if (!roles.includes(role))
      return (
        <ErrorState
          error={new ApiError(403, 'forbidden', 'Seu papel não tem acesso a esta área.')}
        />
      );
    return <DetailPage key={`${kind}-${key}`} kind={kind} id={key} role={role} />;
  }
  const config = ownCollection(key, role === 'creator');
  if (!config) return <Empty title="Página não encontrada" />;
  if (!config.roles.includes(role))
    return (
      <ErrorState error={new ApiError(403, 'forbidden', 'Seu papel não tem acesso a esta área.')} />
    );
  return (
    <>
      <Heading title={config.title} description={config.description}>
        <div className="detail-actions">
          {listActions(key, role).map((action) => (
            <ActionButton key={action.title} action={action} />
          ))}
        </div>
      </Heading>
      <CollectionView
        key={key}
        config={config}
        hideFilters={role === 'creator' && key === 'programs' ? ['program_status'] : []}
      />
    </>
  );
}
const root = createRootRoute({
  component: Root,
  notFoundComponent: () => (
    <Empty title="Página não encontrada">
      <Link to="/app">Voltar ao workspace</Link>
    </Empty>
  ),
  errorComponent: ({ error }) => (
    <ErrorState error={error} retry={() => window.location.reload()} />
  ),
});
const login = createRoute({
  getParentRoute: () => root,
  path: '/login',
  component: () => <AuthPage />,
});
const register = createRoute({
  getParentRoute: () => root,
  path: '/register',
  component: () => <AuthPage register />,
});
const invite = createRoute({
  getParentRoute: () => root,
  path: '/invite/$token',
  component: InvitePage,
});
const app = createRoute({
  getParentRoute: () => root,
  path: '/app',
  beforeLoad: async () => ({ me: await requireSession() }),
  component: Shell,
});
const appPaths = [
  '/',
  'programs',
  'programs/$id',
  'campaigns/$id',
  'commission-plans/$id',
  'applications',
  'applications/$id',
  'memberships',
  'memberships/$id',
  'posts',
  'posts/$id',
  'orders',
  'orders/$id',
  'finance/commissions',
  'finance/ledger',
  'finance/payouts',
  'finance/payout-batches',
  'finance/payout-batches/$id',
  'finance/reconciliation',
  'finance/reconciliation/$id',
  'agent/findings',
  'agent/findings/$id',
  'agent/proposals',
  'agent/proposals/$id',
  'reports',
  'audit',
];
const index = createRoute({ getParentRoute: () => root, path: '/', component: () => <AuthPage /> });
export const router = createRouter({
  routeTree: root.addChildren([
    index,
    login,
    register,
    invite,
    app.addChildren(
      appPaths.map((path) =>
        createRoute({
          getParentRoute: () => app,
          path,
          beforeLoad: ({ context }) => {
            const key = path.replace('/$id', '').split('/').at(-1)!;
            const roles =
              collections[key]?.roles ??
              (key === 'memberships' && !path.includes('$id')
                ? ['owner', 'ops', 'creator']
                : undefined);
            if (roles && !roles.includes(roleOf(context.me))) {
              throw new ApiError(403, 'forbidden', 'Seu papel não tem acesso a esta área.');
            }
          },
          validateSearch: (search: Record<string, unknown>) => search,
          component: Page,
        }),
      ),
    ),
  ]),
  defaultPreload: 'intent',
  defaultPendingComponent: Loading,
});
