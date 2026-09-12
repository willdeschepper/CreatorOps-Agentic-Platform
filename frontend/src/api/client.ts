import { QueryClient, queryOptions } from '@tanstack/react-query';
import type { components } from './schema';
export type Schema<K extends keyof components['schemas']> = components['schemas'][K];
export const API = 'http://localhost:8000';
// Vite forwards development requests to the same local API. Built assets use
// the documented API origin directly, without requiring a Node backend.
const REQUEST_BASE = import.meta.env.DEV ? '/api' : API;
const TOKEN = 'creatorops.session.v1';
export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN),
  set: (token: string) => sessionStorage.setItem(TOKEN, token),
  clear: () => sessionStorage.removeItem(TOKEN),
};
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    detail: string,
    public requestId?: string,
    public fields?: { loc: (string | number)[]; msg: string }[],
  ) {
    super(detail);
  }
}
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 20_000, retry: false, refetchOnWindowFocus: true },
    mutations: { retry: false, gcTime: 0 },
  },
});
export function clearSession() {
  tokenStore.clear();
  void queryClient.cancelQueries();
  queryClient.clear();
  window.dispatchEvent(new Event('creatorops:logout'));
}
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = ['/v1/auth/token', '/v1/auth/register'].includes(path) ? null : tokenStore.get();
  const headers = new Headers(options.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${REQUEST_BASE}${path}`, {
    ...options,
    headers,
    cache: 'no-store',
    referrerPolicy: 'no-referrer',
  }).catch((error: unknown) => {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError(
      0,
      'network_error',
      'A API local não está acessível. Verifique se a stack está ativa e tente atualizar.',
    );
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) clearSession();
    const fields = Array.isArray(data?.detail) ? data.detail : undefined;
    throw new ApiError(
      response.status,
      data?.code ?? 'request_failed',
      fields
        ? 'Revise os campos informados.'
        : (data?.detail ?? 'Não foi possível concluir a solicitação.'),
      response.headers.get('x-request-id') ??
        data?.meta?.request_id ??
        response.headers.get('x-correlation-id') ??
        undefined,
      fields,
    );
  }
  return data as T;
}
export const keys = { resource: (path: string) => ['api', path] as const };
export function resourceOptions<T>(path: string) {
  return queryOptions({
    queryKey: keys.resource(path),
    queryFn: ({ signal }) => request<T>(path, { signal }),
  });
}
export async function command<T>(path: string, body?: unknown) {
  const value = await request<T>(path, {
    method: 'POST',
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  await queryClient.invalidateQueries({ queryKey: ['api'] });
  return value;
}
export type Page<T> = { items: T[]; total: number; limit: number; offset: number };
