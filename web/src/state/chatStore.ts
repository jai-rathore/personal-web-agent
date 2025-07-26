import { create } from 'zustand';
import { ChatStore, ChatState } from '../types';

const generateId = () => Math.random().toString(36).substr(2, 9);

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  state: 'idle',
  sessionId: null,
  isStreaming: false,
  currentToolProposal: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: generateId(),
          timestamp: new Date(),
        },
      ],
    })),

  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages];
      if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage.role === 'assistant') {
          messages[messages.length - 1] = {
            ...lastMessage,
            content,
          };
        }
      }
      return { messages };
    }),

  setState: (newState: ChatState) => set({ state: newState }),

  setToolProposal: (tool) => set({ currentToolProposal: tool }),

  setStreaming: (streaming) => set({ isStreaming: streaming }),

  reset: () =>
    set({
      messages: [],
      state: 'idle',
      sessionId: null,
      isStreaming: false,
      currentToolProposal: null,
    }),
}))