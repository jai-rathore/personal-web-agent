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

const starterChips = [
  "What is Jai's background?",
  "Tell me about his skills",
  "What projects has he worked on?",
  "Schedule a meeting with Jai",
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
  const [isWaitingForFirstToken, setIsWaitingForFirstToken] = useState(false);

  const handleSendMessage = useCallback(async (content: string) => {
    // Add user message
    addMessage({ role: 'user', content });
    
    // Transition from idle to chatting state
    if (state === 'idle') {
      setState('chatting');
    }

    // Prepare messages for API
    const apiMessages = [
      ...messages.map(m => ({ role: m.role, content: m.content })),
      { role: 'user' as const, content }
    ];

    setStreaming(true);
    setIsWaitingForFirstToken(true);
    
    // Add empty assistant message to update
    addMessage({ role: 'assistant', content: '' });
    
    try {
      let fullContent = '';
      
      for await (const chunk of sseClient.streamChat(config.api.baseUrl, apiMessages)) {
        if (chunk.type === 'guardrail') {
          setState('guardrail');
          setStreaming(false);
          setIsWaitingForFirstToken(false);
          updateLastMessage(chunk.content || '');
          return;
        }
        
        if (chunk.type === 'tool_call' && chunk.tool) {
          setToolProposal({
            name: chunk.tool.name,
            args: chunk.tool.parameters
          });
          setState('tool-proposal');
          setStreaming(false);
          setIsWaitingForFirstToken(false);
          return;
        }
        
        if (chunk.type === 'error') {
          updateLastMessage(chunk.content || 'An error occurred');
          setStreaming(false);
          setIsWaitingForFirstToken(false);
          return;
        }
        
        if (chunk.content && chunk.type === 'text') {
          // First token received, stop showing spinner
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
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentToolProposal.args),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result: CreateMeetingResponse = await response.json();
      
      // Add success message
      addMessage({
        role: 'assistant',
        content: `Great! I've scheduled the meeting "${currentToolProposal.args.title}" for you. You should receive a calendar invitation at ${currentToolProposal.args.attendeeEmail}. You can view the event details here: ${result.htmlLink}`,
      });
      
      // Reset state
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

  const handleStarterChip = useCallback((chip: string) => {
    handleSendMessage(chip);
  }, [handleSendMessage]);

  return (
    <div className="flex flex-col h-full">
      {state === 'idle' ? (
        // Initial centered layout
        <div className="flex-1 flex flex-col justify-center items-center px-4">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Hi! I'm Jai's personal web agent.
            </h2>
            <p className="text-lg text-gray-600">
              Ask me about his background, skills, projects, or schedule a meeting.
            </p>
          </div>
          
          <div className="w-full max-w-2xl mb-8">
            <Composer onSend={handleSendMessage} isStreaming={isStreaming} />
          </div>
          
          <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
            {starterChips.map((chip, index) => (
              <button
                key={index}
                onClick={() => handleStarterChip(chip)}
                className="starter-chip"
                disabled={isStreaming}
              >
                {chip}
              </button>
            ))}
          </div>
        </div>
      ) : (
        // Chat layout with messages and docked composer
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
          
          <div className="bg-white border-t border-gray-200 p-4">
            <div className="max-w-4xl mx-auto">
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