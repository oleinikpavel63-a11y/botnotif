import type { ReactNode } from 'react';

import { useAuth } from '../hooks/useAuth';
import type { Role } from '../types/contracts';

/**
 * Renders `children` only when the current user's role satisfies `allow`.
 * Convenience gating only — the backend re-checks every mutation.
 */
export function RoleGate({
  allow,
  children,
  fallback = null,
}: {
  allow: (role: Role) => boolean;
  children: ReactNode;
  fallback?: ReactNode;
}): JSX.Element {
  const { user } = useAuth();
  if (!user || !allow(user.role)) return <>{fallback}</>;
  return <>{children}</>;
}
