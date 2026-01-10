import React, { useState } from 'react';
import Navigation from '../components/Navigation';
import api from '../services/api';

function Integrations() {
  const [loading, setLoading] = useState(false);

  const handleConnectGmail = async () => {
    try {
      const response = await api.get('/integrations/gmail/auth-url');
      window.location.href = response.data.url;
    } catch (error) {
      alert('Failed to get Gmail authorization URL');
    }
  };

  const handleConnectCalendar = async () => {
    try {
      const response = await api.get('/integrations/calendar/auth-url');
      window.location.href = response.data.url;
    } catch (error) {
      alert('Failed to get Calendar authorization URL');
    }
  };

  const handleConnectDrive = async () => {
    try {
      const response = await api.get('/integrations/drive/auth-url');
      window.location.href = response.data.url;
    } catch (error) {
      alert('Failed to get Drive authorization URL');
    }
  };

  const handleSyncNow = async () => {
    setLoading(true);
    try {
      await api.post('/integrations/sync');
      alert('Sync started! Check your time entries for new suggestions.');
    } catch (error) {
      alert('Failed to start sync');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navigation />
      <div className="container">
        <h1>Integrations</h1>
        <p style={{ marginBottom: '2rem', color: '#7f8c8d' }}>
          Connect your email, calendar, and document systems to automatically track your time.
        </p>

        <div className="card">
          <h2>Email Integration</h2>
          <p>Track sent emails and automatically create time entry suggestions.</p>
          <button onClick={handleConnectGmail} className="btn btn-primary">
            Connect Gmail
          </button>
        </div>

        <div className="card">
          <h2>Calendar Integration</h2>
          <p>Track meetings and scheduled events as billable time.</p>
          <button onClick={handleConnectCalendar} className="btn btn-primary">
            Connect Google Calendar
          </button>
        </div>

        <div className="card">
          <h2>Document Integration</h2>
          <p>Track document edits and file modifications.</p>
          <button onClick={handleConnectDrive} className="btn btn-primary">
            Connect Google Drive
          </button>
        </div>

        <div className="card">
          <h2>Manual Sync</h2>
          <p>Trigger a manual sync of all connected services.</p>
          <button onClick={handleSyncNow} className="btn btn-success" disabled={loading}>
            {loading ? 'Syncing...' : 'Sync Now'}
          </button>
        </div>

        <div className="card" style={{ backgroundColor: '#fff3cd', borderLeft: '4px solid #ffc107' }}>
          <h3>⚠️ Setup Required</h3>
          <p>
            To use integrations, you need to configure OAuth credentials in your environment variables.
            See the documentation for setup instructions.
          </p>
        </div>
      </div>
    </>
  );
}

export default Integrations;
