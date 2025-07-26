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
    const durationMs = endDate.getTime() - startDate.getTime();
    const durationMinutes = Math.round(durationMs / 60000);
    
    if (durationMinutes < 60) {
      return `${durationMinutes} minutes`;
    } else {
      const hours = Math.floor(durationMinutes / 60);
      const minutes = durationMinutes % 60;
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours} hour${hours > 1 ? 's' : ''}`;
    }
  };

  return (
    <div className="max-w-md mx-auto my-4 bg-white border border-gray-200 rounded-lg shadow-sm">
      <div className="p-6">
        <div className="flex items-start mb-4">
          <svg className="w-6 h-6 text-blue-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Meeting Proposal</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <p><span className="font-medium">Title:</span> {action.title}</p>
              <p><span className="font-medium">Date & Time:</span> {formatDateTime(action.startIso)}</p>
              <p><span className="font-medium">Duration:</span> {getDuration(action.startIso, action.endIso)}</p>
              <p><span className="font-medium">Attendee:</span> {action.attendeeEmail}</p>
            </div>
            <p className="mt-3 text-xs text-gray-500">
              <svg className="inline w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Times shown in your local timezone. Meeting will be scheduled in PT.
            </p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
          >
            Confirm Meeting
          </button>
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-md hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActionCard;