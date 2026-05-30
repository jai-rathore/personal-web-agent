import React from 'react';

const GuardrailNotice: React.FC = () => {
  return (
    <div className="max-w-md mx-auto my-4 bg-amber-50/80 border border-amber-200/60 rounded-2xl p-4 animate-fade-in">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center flex-shrink-0">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-medium text-amber-800 mb-1">Outside my scope</h4>
          <p className="text-sm text-amber-700 leading-relaxed">
            I can share Jai's background, propose or book meetings, and provide contact info.
            How can I help within those areas?
          </p>
        </div>
      </div>
    </div>
  );
};

export default GuardrailNotice;
