import { useEffect } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';

import { queryClient } from './lib/queryClient';
import { initTelegram } from './lib/telegram';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ConfirmProvider } from './hooks/useConfirm';
import { SSEProvider } from './hooks/useSSE';
import { ToastProvider } from './hooks/useToast';
import { useTheme } from './hooks/useTheme';
import { ToastContainer } from './components/ToastContainer';
import { Spinner } from './components/ui';
import { Login } from './pages/Login';
import { router } from './router';

/** Full-screen loading state shown during the auth handshake. */
function AuthLoading(): JSX.Element {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-surface text-primary dark:bg-[#0c110d] dark:text-accent">
      <div className="text-4xl" aria-hidden>
        📣
      </div>
      <Spinner className="h-8 w-8" />
      <p className="text-sm text-ink/60 dark:text-surface/60">Подключение…</p>
    </div>
  );
}

/** Gates the app on authentication; wires the live providers once signed in. */
function Gate(): JSX.Element {
  const { status, error, retry } = useAuth();

  if (status === 'loading') return <AuthLoading />;
  if (status === 'no-init-data' || status === 'error') {
    return <Login status={status} error={error} onRetry={retry} />;
  }

  // Authenticated: SSE + toast + confirm providers wrap the routed app.
  return (
    <SSEProvider>
      <ToastProvider>
        <ConfirmProvider>
          <RouterProvider router={router} />
          <ToastContainer />
        </ConfirmProvider>
      </ToastProvider>
    </SSEProvider>
  );
}

export function App(): JSX.Element {
  useTheme();

  useEffect(() => {
    initTelegram();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Gate />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
