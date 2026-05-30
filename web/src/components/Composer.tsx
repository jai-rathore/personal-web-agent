import React, { useState, useRef, useEffect } from 'react';

interface ComposerProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
  isDocked?: boolean;
}

const Composer: React.FC<ComposerProps> = ({ onSend, isStreaming, isDocked = false }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        textareaRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isStreaming) {
      onSend(message.trim());
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={isDocked ? 'w-full' : 'w-full max-w-2xl mx-auto'}
    >
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            adjustTextareaHeight();
          }}
          onKeyDown={handleKeyDown}
          placeholder="Ask about Jai's background, skills, or schedule a meeting..."
          className="w-full px-4 py-3 pr-12 bg-white border border-slate-200 rounded-xl resize-none
                     focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-400
                     text-sm sm:text-base text-slate-800 placeholder-slate-400
                     shadow-sm transition-shadow duration-200
                     hover:shadow-md focus:shadow-md"
          rows={1}
          disabled={isStreaming}
        />
        <button
          type="submit"
          disabled={!message.trim() || isStreaming}
          className="absolute right-2 bottom-2 p-2 text-white bg-brand-600 rounded-lg
                     hover:bg-brand-700 disabled:bg-slate-300 disabled:cursor-not-allowed
                     transition-colors shadow-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
          </svg>
        </button>
      </div>
      <p className="mt-2 text-xs text-slate-400 text-center">
        <span className="hidden sm:inline">Enter to send &middot; Shift+Enter for new line &middot; &#8984;K to focus</span>
        <span className="sm:hidden">Tap send or press return</span>
      </p>
    </form>
  );
};

export default Composer;
