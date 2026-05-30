import React from 'react';
import { CreateMeetingArgs } from '../types';

interface ActionCardProps {
  action: CreateMeetingArgs;
  onConfirm: () => void;
  onCancel: () => void;
}

const ActionCard: React.FC<ActionCardProps> = ({ action, onConfirm, onCancel }) => {
  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    const options: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short',
    };
    return date.toLocaleString('en-US', options);
  };

  const getDuration = (start: string, end: string) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const durationMinutes = Math.round((endDate.getTime() - startDate.getTime()) / 60000);

    if (durationMinutes < 60) {
      return `${durationMinutes} minutes`;
    }
    const hours = Math.floor(durationMinutes / 60);
    const minutes = durationMinutes % 60;
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours} hour${hours > 1 ? 's' : ''}`;
  };

  return (
    <div className="max-w-md mx-auto my-4 bg-white border border-slate-200/80 rounded-2xl shadow-sm animate-fade-in">
      <div className="p-5 sm:p-6">
        <div className="flex items-start gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-slate-900 mb-3">Meeting Proposal</h3>
            <div className="space-y-2 text-sm text-slate-600">
              <p><span className="font-medium text-slate-700">Title:</span> {action.title}</p>
              <p><span className="font-medium text-slate-700">When:</span> {formatDateTime(action.startIso)}</p>
              <p><span className="font-medium text-slate-700">Duration:</span> {getDuration(action.startIso, action.endIso)}</p>
              <p><span className="font-medium text-slate-700">Attendee:</span> {action.attendeeEmail}</p>
            </div>
            <p className="mt-3 text-xs text-slate-400 flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Times shown in your local timezone. Meeting scheduled in PT.
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-xl hover:bg-brand-700 transition-colors shadow-sm"
          >
            Confirm
          </button>
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 bg-slate-100 text-slate-700 text-sm font-medium rounded-xl hover:bg-slate-200 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActionCard;
