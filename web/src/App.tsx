import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import ChatShell from './components/ChatShell';
import PrivacyPage from './components/PrivacyPage';

const App: React.FC = () => {
  return (
    <Router>
      <div className="h-full flex flex-col">
        <Routes>
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route 
            path="/" 
            element={
              <>
                <Header />
                <main className="flex-1 pt-16 pb-12 overflow-hidden">
                  <ChatShell />
                </main>
                <Footer />
              </>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
};

export default App;