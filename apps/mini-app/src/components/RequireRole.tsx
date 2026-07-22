import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';

import { useAuth } from '../hooks/useAuth';
import type { Role } from '../types/contracts';

/**
 * Route guard: redirects to Home if the current role fails `allow`. This keeps
 * e.g. OPERATOR out of /users entirely — the backend also rejects the calls.
 */
export function RequireRole({
  allow,
  children,
}: {
  allow: (role: Role) => boolean;
  children: ReactNode;
}): JSX.Element {
  const { user } = useAuth();
  if (!user || !allow(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}
