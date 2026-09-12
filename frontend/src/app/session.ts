import { redirect } from '@tanstack/react-router';
import { queryClient, request, tokenStore, type Schema } from '../api/client';
export type Me = Schema<'MeResponse'>;
export type Role = 'owner' | 'ops' | 'finance' | 'creator';
export const meOptions = () => ({
  queryKey: ['session'],
  queryFn: ({ signal }: { signal: AbortSignal }) => request<Me>('/v1/auth/me', { signal }),
  staleTime: 30_000,
  retry: false as const,
});
export const roleOf = (me: Me): Role => (me.kind === 'creator' ? 'creator' : me.role!);
export async function requireSession() {
  if (!tokenStore.get()) throw redirect({ to: '/login' });
  try {
    return await queryClient.fetchQuery(meOptions());
  } catch (error) {
    if (!tokenStore.get()) throw redirect({ to: '/login' });
    throw error;
  }
}
export const staff: Role[] = ['owner', 'ops', 'finance'];
export const operators: Role[] = ['owner', 'ops'];
export const financiers: Role[] = ['owner', 'finance'];
