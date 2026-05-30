import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import FeedbackModal from './FeedbackModal';

const Footer: React.FC = () => {
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);

  return (
    <>
      <footer className="bg-white/80 backdrop-blur-lg border-t border-slate-200/60">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="flex justify-center items-center h-10 text-xs text-slate-400 gap-4">
            <Link to="/privacy" className="hover:text-slate-600 transition-colors">
              Privacy
            </Link>
            <span className="text-slate-200">|</span>
            <button
              onClick={() => setIsFeedbackModalOpen(true)}
              className="hover:text-slate-600 transition-colors"
            >
              Feedback
            </button>
          </div>
        </div>
      </footer>

      <FeedbackModal
        isOpen={isFeedbackModalOpen}
        onClose={() => setIsFeedbackModalOpen(false)}
      />
    </>
  );
};

export default Footer;
