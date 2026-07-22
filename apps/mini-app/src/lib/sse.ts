/**
 * Server-Sent Events client for `GET /api/admin/events?token=<jwt>`.
 *
 * EventSource cannot set an Authorization header, so the backend accepts the
 * access token as a query parameter. We parse each `device_state` /
 * `command_update` / `sync_status` frame with zod and forward it to a handler.
 * On error the browser's EventSource auto-reconnects; we also surface a
 * connected/disconnected signal so the UI can fall back to polling.
 */
import { SSE_URL } from './config';
import { adminEventSchema } from '../types/schemas';
import type { AdminEvent } from '../types/contracts';

export interface SseHandlers {
  onEvent(event: AdminEvent): void;
  onOpen?(): void;
  onError?(): void;
}

export class SseClient {
  private source: EventSource | null = null;
  private closedByUser = false;

  constructor(private readonly handlers: SseHandlers) {}

  start(token: string): void {
    if (this.source) return;
    this.closedByUser = false;

    const url = `${SSE_URL}?token=${encodeURIComponent(token)}`;
    const source = new EventSource(url);
    this.source = source;

    source.onopen = () => {
      if (!this.closedByUser) this.handlers.onOpen?.();
    };

    source.onmessage = (msg: MessageEvent<string>) => {
      if (!msg.data) return;
      let json: unknown;
      try {
        json = JSON.parse(msg.data);
      } catch {
        return; // keep-alive / hello frames with non-JSON payloads
      }
      const parsed = adminEventSchema.safeParse(json);
      if (parsed.success) this.handlers.onEvent(parsed.data);
    };

    source.onerror = () => {
      if (!this.closedByUser) this.handlers.onError?.();
      // EventSource handles reconnection itself while readyState !== CLOSED.
    };
  }

  stop(): void {
    this.closedByUser = true;
    this.source?.close();
    this.source = null;
  }
}
