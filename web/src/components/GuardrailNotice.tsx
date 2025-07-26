import React from 'react';

const GuardrailNotice: React.FC = () => {
  return (
    <div className="max-w-md mx-auto my-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
      <div className="flex items-start">
        <svg className="w-5 h-5 text-amber-600 mr-3 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div className="flex-1">
          <h4 className="text-sm font-medium text-amber-800 mb-1">Request Outside Scope</h4>
          <p className="text-sm text-amber-700">
            This assistant handles questions about Jai and simple actions it's authorized to perform 
            (share his background, propose or book time, or provide contact options). 
            What should it help with?
          </p>
        </div>
      </div>
    </div>
  );
};

export default GuardrailNotice;