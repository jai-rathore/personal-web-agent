interface SSEMessage {
  role: 'assistant';
  content?: string;
  type?: 'text' | 'tool_call' | 'guardrail' | 'error' | 'connected';
  tool?: {
    name: string;
    parameters: any;
  };
}

export class SSEClient {
  private controller: AbortController | null = null;

  async* streamChat(
    apiBase: string,
    messages: Array<{ role: string; content: string }>,
    sessionId?: string
  ): AsyncGenerator<SSEMessage, void, unknown> {
    this.controller = new AbortController();

    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages,
          sessionId,
        }),
        signal: this.controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }
            try {
              const message = JSON.parse(data);
              // Skip connected messages
              if (message.type === 'connected') {
                continue;
              }
              yield message as SSEMessage;
            } catch (e) {
              console.error('Failed to parse SSE message:', e, 'Data:', data);
            }
          }
        }
      }
    } finally {
      this.controller = null;
    }
  }

  abort() {
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }
  }
}