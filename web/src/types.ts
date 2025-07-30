export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  toolCall?: ToolCall;
}

export interface ToolCall {
  name: string;
  args: CreateMeetingArgs;
}

export interface CreateMeetingArgs {
  title: string;
  startIso: string;
  endIso: string;
  attendeeEmail: string;
}

export interface ChatRequest {
  messages: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
  }>;
  sessionId?: string;
}

export interface CreateMeetingResponse {
  status: 'confirmed';
  eventId: string;
  htmlLink: string;
}

export type ChatState = 'idle' | 'chatting' | 'tool-proposal' | 'guardrail';

export interface ChatStore {
  messages: Message[];
  state: ChatState;
  sessionId: string | null;
  isStreaming: boolean;
  currentToolProposal: ToolCall | null;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateLastMessage: (content: string) => void;
  setState: (state: ChatState) => void;
  setToolProposal: (tool: ToolCall | null) => void;
  setStreaming: (streaming: boolean) => void;
  reset: () => void;
}

export interface FeedbackRequest {
  message: string;
  name?: string;
  email?: string;
  page?: string;
}

export interface FeedbackResponse {
  status: string;
  message: string;
  id?: string;
}