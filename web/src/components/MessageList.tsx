import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Message } from '../types';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  isWaitingForFirstToken?: boolean;
}

const AssistantAvatar: React.FC = () => (
  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center flex-shrink-0 shadow-sm">
    <span className="text-white text-xs font-bold">J</span>
  </div>
);

const ThinkingDots: React.FC = () => (
  <div className="thinking-dots">
    <div className="thinking-dot animate-dot-bounce-1" />
    <div className="thinking-dot animate-dot-bounce-2" />
    <div className="thinking-dot animate-dot-bounce-3" />
  </div>
);

const MessageList: React.FC<MessageListProps> = ({ messages, isStreaming, isWaitingForFirstToken = false }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-3xl mx-auto space-y-5">
        {messages.map((message) => {
          const isUser = message.role === 'user';
          const isLast = message === messages[messages.length - 1];
          const isAssistant = message.role === 'assistant';

          return (
            <div
              key={message.id}
              className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {isAssistant && <AssistantAvatar />}

              <div
                className={`message-bubble ${
                  isUser ? 'message-user' : 'message-assistant'
                }`}
              >
                <div className="prose-chat text-[0.9375rem] leading-relaxed">
                  {isUser ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                        a: ({ href, children }) => (
                          <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-brand-600 underline underline-offset-2 hover:text-brand-700"
                          >
                            {children}
                          </a>
                        ),
                        ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                        li: ({ children }) => <li>{children}</li>,
                        code: ({ children }) => (
                          <code className="bg-slate-100 text-slate-800 px-1.5 py-0.5 rounded text-sm font-mono">
                            {children}
                          </code>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  )}
                </div>

                {isAssistant && isLast && (
                  <>
                    {isWaitingForFirstToken ? (
                      <ThinkingDots />
                    ) : isStreaming && message.content && (
                      <span className="inline-block w-0.5 h-4 bg-brand-400 animate-pulse ml-0.5 rounded-full" />
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default MessageList;
