import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalClients: 0,
    activeMatters: 0,
    pendingSuggestions: 0,
    unpaidInvoices: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const [clients, matters, timeEntries, invoices] = await Promise.all([
        api.get('/clients'),
        api.get('/matters'),
        api.get('/time-entries?status=suggested'),
        api.get('/invoices'),
      ]);

      setStats({
        totalClients: clients.data.length,
        activeMatters: matters.data.filter(m => m.status === 'active').length,
        pendingSuggestions: timeEntries.data.length,
        unpaidInvoices: invoices.data.filter(i => i.status !== 'paid').length,
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      await api.post('/integrations/sync');
      alert('Sync started! Check back in a few minutes for new suggestions.');
    } catch (error) {
      alert('Failed to start sync');
    }
  };

  if (loading) {
    return (
      <>
        <Navigation />
        <div className="container">
          <div className="loading">Loading...</div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navigation />
      <div className="container">
        <h1>Welcome, {user?.firstName}!</h1>
        <p style={{ marginBottom: '2rem', color: '#7f8c8d' }}>
          Overview of your billing and time tracking
        </p>

        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Clients</h3>
            <p>{stats.totalClients}</p>
          </div>
          <div className="stat-card">
            <h3>Active Matters</h3>
            <p>{stats.activeMatters}</p>
          </div>
          <div className="stat-card">
            <h3>Pending Suggestions</h3>
            <p>{stats.pendingSuggestions}</p>
          </div>
          <div className="stat-card">
            <h3>Unpaid Invoices</h3>
            <p>{stats.unpaidInvoices}</p>
          </div>
        </div>

        <div className="card">
          <h2>Quick Actions</h2>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button onClick={handleSync} className="btn btn-primary">
              Sync Activities
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default Dashboard;
