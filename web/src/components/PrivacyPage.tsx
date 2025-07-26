import React from 'react';
import { Link } from 'react-router-dom';
import { config } from '../config';

const PrivacyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-16">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-sm p-8">
          <Link
            to="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-6"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Chat
          </Link>
          
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Privacy Policy</h1>
          
          <div className="prose prose-gray max-w-none">
            <p className="text-gray-600 mb-6">
              Last updated: {new Date().toLocaleDateString()}
            </p>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Information We Collect</h2>
              <p className="text-gray-700 mb-4">
                We collect minimal information necessary to provide our service:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>IP addresses for security and rate limiting purposes (retained ≤30 days)</li>
                <li>Chat messages you send (processed by AI but not stored)</li>
                <li>Meeting details when you confirm calendar appointments</li>
              </ul>
            </section>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">How We Use Information</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Chat messages are processed by AI to provide responses about Jai</li>
                <li>IP addresses are used for security monitoring and abuse prevention</li>
                <li>Meeting information is used to create calendar events when requested</li>
              </ul>
            </section>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Retention</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Chat messages are not permanently stored</li>
                <li>IP addresses are retained for up to 30 days</li>
                <li>Calendar events persist according to your calendar settings</li>
              </ul>
            </section>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Tracking and Cookies</h2>
              <p className="text-gray-700">
                This site does not use cookies or persistent tracking technologies. 
                Each chat session is independent and temporary.
              </p>
            </section>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Rights</h2>
              <p className="text-gray-700 mb-4">
                You have the right to:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Request deletion of any personal data we may have</li>
                <li>Ask questions about how your data is processed</li>
                <li>Contact us about privacy concerns</li>
              </ul>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Contact</h2>
              <p className="text-gray-700">
                For data deletion requests or privacy questions, contact:{' '}
                <a href={`mailto:${config.contact.email}`} className="text-blue-600 hover:text-blue-700">
                  {config.contact.email}
                </a>
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPage;