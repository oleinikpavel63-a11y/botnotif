import { createHashRouter, Navigate } from 'react-router-dom';

import { Layout } from './components/Layout';
import { RequireRole } from './components/RequireRole';
import { canViewAudit, canViewUsers } from './lib/roles';
import { Audit } from './pages/Audit';
import { Devices } from './pages/Devices';
import { Home } from './pages/Home';
import { Music } from './pages/Music';
import { Scenarios } from './pages/Scenarios';
import { Schedule } from './pages/Schedule';
import { Settings } from './pages/Settings';
import { Users } from './pages/Users';

/**
 * Hash router: robust under the `/app` static mount and inside the Telegram
 * webview (no server-side route config or basename juggling required).
 */
export const router = createHashRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'music', element: <Music /> },
      { path: 'scenarios', element: <Scenarios /> },
      { path: 'schedule', element: <Schedule /> },
      { path: 'devices', element: <Devices /> },
      {
        path: 'users',
        element: (
          <RequireRole allow={canViewUsers}>
            <Users />
          </RequireRole>
        ),
      },
      {
        path: 'audit',
        element: (
          <RequireRole allow={canViewAudit}>
            <Audit />
          </RequireRole>
        ),
      },
      { path: 'settings', element: <Settings /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
