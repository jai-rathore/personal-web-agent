import React, { useState, useCallback } from 'react';
import { flushSync } from 'react-dom';
import { useChatStore } from '../state/chatStore';
import { SSEClient } from '../lib/sse';
import { config } from '../config';
import Composer from './Composer';
import MessageList from './MessageList';
import ActionCard from './ActionCard';
import GuardrailNotice from './GuardrailNotice';
import { CreateMeetingResponse } from '../types';

const starterCards = [
  {
    label: "What is Jai's background?",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
      </svg>
    ),
    color: 'bg-blue-50 text-blue-600',
  },
  {
    label: 'Tell me about his skills',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
      </svg>
    ),
    color: 'bg-violet-50 text-violet-600',
  },
  {
    label: 'What projects has he worked on?',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
      </svg>
    ),
    color: 'bg-emerald-50 text-emerald-600',
  },
  {
    label: 'Schedule a meeting with Jai',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
      </svg>
    ),
    color: 'bg-amber-50 text-amber-600',
  },
];

const ChatShell: React.FC = () => {
  const {
    messages,
    state,
    isStreaming,
    currentToolProposal,
    addMessage,
    updateLastMessage,
    setState,
    setToolProposal,
    setStreaming,
  } = useChatStore();

  const [sseClient] = useState(() => new SSEClient());
  const [sessionId] = useState(() => crypto.randomUUID());
  const [isWaitingForFirstToken, setIsWaitingForFirstToken] = useState(false);

  const handleSendMessage = useCallback(async (content: string) => {
    addMessage({ role: 'user', content });

    if (state === 'idle' || state === 'guardrail') {
      setState('chatting');
    }

    const apiMessages = [
      ...messages.map(m => ({ role: m.role, content: m.content })),
      { role: 'user' as const, content }
    ];

    setStreaming(true);
    setIsWaitingForFirstToken(true);
    addMessage({ role: 'assistant', content: '' });

    try {
      let fullContent = '';

      for await (const chunk of sseClient.streamChat(config.api.baseUrl, apiMessages, sessionId)) {
        if (chunk.type === 'guardrail') {
          setState('guardrail');
          setStreaming(false);
          setIsWaitingForFirstToken(false);
          updateLastMessage(chunk.content || '');
          return;
        }

        // Tool calls like schedule_calendly_meeting are auto-executed by ADK;
        // the agent will follow up with a text response containing the result.
        // Only intercept if a tool explicitly requires user confirmation.
        if (chunk.type === 'tool_call' && chunk.tool) {
          if (chunk.tool.name === 'create_meeting') {
            setToolProposal({ name: chunk.tool.name, args: chunk.tool.parameters });
            setState('tool-proposal');
            setStreaming(false);
            setIsWaitingForFirstToken(false);
            return;
          }
          // For all other tools, let the stream continue — ADK handles execution
          continue;
        }

        if (chunk.type === 'error') {
          updateLastMessage(chunk.content || 'An error occurred');
          setStreaming(false);
          setIsWaitingForFirstToken(false);
          return;
        }

        if (chunk.content && chunk.type === 'text') {
          if (isWaitingForFirstToken) {
            flushSync(() => {
              setIsWaitingForFirstToken(false);
            });
          }
          fullContent += chunk.content;
          flushSync(() => {
            updateLastMessage(fullContent);
          });
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      updateLastMessage('Sorry, there was an error processing your request.');
    } finally {
      setStreaming(false);
      setIsWaitingForFirstToken(false);
    }
  }, [messages, state, addMessage, updateLastMessage, setState, setToolProposal, setStreaming, sseClient]);

  const handleConfirmAction = useCallback(async () => {
    if (!currentToolProposal) return;

    try {
      const response = await fetch(`${config.api.baseUrl}/actions/create-meeting`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentToolProposal.args),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: CreateMeetingResponse = await response.json();

      addMessage({
        role: 'assistant',
        content: `Great! I've scheduled the meeting "${currentToolProposal.args.title}" for you. You should receive a calendar invitation at ${currentToolProposal.args.attendeeEmail}. You can view the event details here: ${result.htmlLink}`,
      });

      setToolProposal(null);
      setState('chatting');
    } catch (error) {
      console.error('Meeting creation error:', error);
      addMessage({
        role: 'assistant',
        content: 'Sorry, there was an error creating the meeting. Please try again or contact Jai directly.',
      });
      setToolProposal(null);
      setState('chatting');
    }
  }, [currentToolProposal, addMessage, setToolProposal, setState]);

  const handleCancelAction = useCallback(() => {
    addMessage({
      role: 'assistant',
      content: 'No problem! The meeting has been cancelled. Is there anything else I can help you with regarding Jai\'s availability or background?',
    });
    setToolProposal(null);
    setState('chatting');
  }, [addMessage, setToolProposal, setState]);

  const handleStarterCard = useCallback((label: string) => {
    handleSendMessage(label);
  }, [handleSendMessage]);

  return (
    <div className="flex flex-col h-full">
      {state === 'idle' ? (
        /* ── Landing / Idle ─────────────────────────────────────────── */
        <div className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6">
          {/* Avatar + greeting */}
          <div className="animate-fade-in-up text-center mb-10">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center mx-auto mb-5 shadow-lg shadow-brand-200">
              <span className="text-2xl font-bold text-white">J</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-2 tracking-tight">
              Hey, I'm Jai's web agent
            </h1>
            <p className="text-base text-slate-500 max-w-md mx-auto">
              I can tell you about his background, skills, projects, or help schedule a meeting.
            </p>
          </div>

          {/* Composer */}
          <div className="w-full max-w-2xl mb-8 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            <Composer onSend={handleSendMessage} isStreaming={isStreaming} />
          </div>

          {/* Starter cards grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            {starterCards.map((card, index) => (
              <button
                key={index}
                onClick={() => handleStarterCard(card.label)}
                className="starter-card"
                disabled={isStreaming}
              >
                <div className={`starter-card-icon ${card.color}`}>
                  {card.icon}
                </div>
                <span>{card.label}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* ── Active Chat ────────────────────────────────────────────── */
        <>
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            isWaitingForFirstToken={isWaitingForFirstToken}
          />

          {state === 'tool-proposal' && currentToolProposal && (
            <div className="px-4 py-2">
              <ActionCard
                action={currentToolProposal.args}
                onConfirm={handleConfirmAction}
                onCancel={handleCancelAction}
              />
            </div>
          )}

          {state === 'guardrail' && (
            <div className="px-4 py-2">
              <GuardrailNotice />
            </div>
          )}

          <div className="bg-white/80 backdrop-blur-lg border-t border-slate-200/60 p-3 sm:p-4">
            <div className="max-w-3xl mx-auto">
              <Composer
                onSend={handleSendMessage}
                isStreaming={isStreaming}
                isDocked={true}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatShell;
