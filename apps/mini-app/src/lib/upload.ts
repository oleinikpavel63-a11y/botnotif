/**
 * Multipart upload with real progress reporting via XMLHttpRequest (the fetch
 * API cannot report upload progress). The response is still validated with the
 * shared Track zod schema, mirroring the main API client.
 */
import { ApiError } from './api';
import { API_BASE_URL } from './config';
import { getToken } from './token';
import { apiErrorBodySchema, trackSchema } from '../types/schemas';
import type { Track } from '../types/contracts';

export interface UploadFields {
  title?: string;
  category?: string;
  isAnnouncement?: boolean;
}

export function uploadTrackWithProgress(
  file: File,
  fields: UploadFields,
  onProgress: (ratio: number) => void,
): Promise<Track> {
  return new Promise<Track>((resolve, reject) => {
    const form = new FormData();
    form.append('file', file);
    if (fields.title) form.append('title', fields.title);
    if (fields.category) form.append('category', fields.category);
    form.append('is_announcement', String(Boolean(fields.isAnnouncement)));

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/tracks`);
    const token = getToken();
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(e.loaded / e.total);
    };

    xhr.onload = () => {
      const status = xhr.status;
      if (status >= 200 && status < 300) {
        try {
          const parsed = trackSchema.safeParse(JSON.parse(xhr.responseText));
          if (!parsed.success) {
            reject(
              new ApiError('Сервер вернул неожиданные данные.', {
                kind: 'parse',
                status,
                code: 'schema_mismatch',
              }),
            );
            return;
          }
          resolve(parsed.data);
        } catch {
          reject(new ApiError('Ошибка обработки ответа.', { kind: 'parse', status, code: 'parse_error' }));
        }
        return;
      }
      let message = `Ошибка загрузки (${status}).`;
      let code = `http_${status}`;
      try {
        const body = apiErrorBodySchema.parse(JSON.parse(xhr.responseText));
        message = body.error;
        code = body.code;
      } catch {
        /* keep defaults */
      }
      reject(new ApiError(message, { kind: 'http', status, code }));
    };

    xhr.onerror = () =>
      reject(new ApiError('Нет связи с сервером.', { kind: 'network', status: 0, code: 'network_error' }));

    xhr.send(form);
  });
}
