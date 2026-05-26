const API = '/api';

export type ChatMessage = { role: 'user' | 'assistant'; content: string };

export async function sendChatStream(
  message: string,
  history: ChatMessage[],
  onToken: (content: string) => void,
  onDone: () => void,
  onError: (err: string) => void
): Promise<void> {
  const res = await fetch(`${API}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) {
    onError(`Request failed: ${res.status}`);
    return;
  }
  const reader = res.body?.getReader();
  if (!reader) {
    onError('No response body');
    return;
  }
  const decoder = new TextDecoder();
  let buffer = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'token' && data.content) onToken(data.content);
            if (data.type === 'status') {
              // status events are informational; UI can show a thinking indicator
            }
            if (data.type === 'done') onDone();
            if (data.type === 'error') onError(data.content ?? 'Unknown error');
          } catch {
            // skip invalid json
          }
        }
      }
    }
    if (buffer.startsWith('data: ')) {
      try {
        const data = JSON.parse(buffer.slice(6));
        if (data.type === 'token' && data.content) onToken(data.content);
        if (data.type === 'done') onDone();
        if (data.type === 'error') onError(data.content ?? 'Unknown error');
      } catch {
        // skip
      }
    }
    onDone();
  } catch (e) {
    onError(e instanceof Error ? e.message : String(e));
  }
}

export async function uploadFile(file: File): Promise<{ ok: boolean; message?: string; chunks?: number; detail?: string }> {
  const form = new FormData();
  form.append('upload', file);
  const res = await fetch(`${API}/ingest`, {
    method: 'POST',
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return { ok: false, message: data.detail ?? `Upload failed: ${res.status}` };
  }
  return { ok: data.ok ?? true, message: data.message, chunks: data.chunks };
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
