import React, { useEffect, useRef } from 'react';
import { Message } from '../types';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  isWaitingForFirstToken?: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isStreaming, isWaitingForFirstToken = false }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatContent = (content: string) => {
    // Simple markdown-like formatting
    return content.split('\n').map((line, i) => {
      // Handle bullet points
      if (line.trim().startsWith('- ')) {
        return (
          <li key={i} className="ml-4">
            {line.substring(2)}
          </li>
        );
      }
      // Handle numbered lists
      if (/^\d+\.\s/.test(line.trim())) {
        return (
          <li key={i} className="ml-4">
            {line}
          </li>
        );
      }
      // Regular paragraph
      return line ? (
        <p key={i} className="mb-2">
          {line}
        </p>
      ) : (
        <br key={i} />
      );
    });
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-4xl mx-auto space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`message-bubble ${
                message.role === 'user' ? 'message-user' : 'message-assistant'
              }`}
            >
              <div className="whitespace-pre-wrap">{formatContent(message.content)}</div>
              {message.role === 'assistant' && message === messages[messages.length - 1] && (
                <>
                  {isWaitingForFirstToken ? (
                    <div className="flex items-center mt-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                      <span className="ml-2 text-sm text-gray-500">Thinking...</span>
                    </div>
                  ) : isStreaming && message.content && (
                    <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default MessageList;