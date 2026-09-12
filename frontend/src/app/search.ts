import { useLocation, useNavigate } from '@tanstack/react-router';
export function useSearchState() {
  const location = useLocation();
  const navigate = useNavigate();
  const search = location.search as Record<string, unknown>;
  return {
    search,
    update: (patch: Record<string, unknown>) => {
      const params = new URLSearchParams();
      for (const [key, value] of Object.entries({ ...search, ...patch })) {
        if (value !== undefined && value !== null && value !== '') params.set(key, String(value));
      }
      void navigate({
        href: `${location.pathname}${params.size ? '?' + params : ''}`,
        replace: true,
      });
    },
  };
}
