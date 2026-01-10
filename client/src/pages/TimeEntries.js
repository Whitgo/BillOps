import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import api from '../services/api';

function TimeEntries() {
  const [timeEntries, setTimeEntries] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [entriesRes, suggestionsRes] = await Promise.all([
        api.get('/time-entries?status=approved'),
        api.get('/integrations/suggestions'),
      ]);
      setTimeEntries(entriesRes.data);
      setSuggestions(suggestionsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      await api.post(`/time-entries/${id}/approve`);
      fetchData();
    } catch (error) {
      alert('Failed to approve time entry');
    }
  };

  const handleReject = async (id) => {
    try {
      await api.post(`/time-entries/${id}/reject`);
      fetchData();
    } catch (error) {
      alert('Failed to reject time entry');
    }
  };

  if (loading) {
    return (
      <>
        <Navigation />
        <div className="container"><div className="loading">Loading...</div></div>
      </>
    );
  }

  return (
    <>
      <Navigation />
      <div className="container">
        <h1>Time Entries</h1>

        {suggestions.length > 0 && (
          <>
            <h2 style={{ marginTop: '2rem' }}>Suggested Time Entries</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Duration</th>
                  <th>Matter</th>
                  <th>Amount</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {suggestions.map((entry) => (
                  <tr key={entry.id}>
                    <td>{new Date(entry.date).toLocaleDateString()}</td>
                    <td>{entry.description}</td>
                    <td>{(entry.duration / 60).toFixed(2)}h</td>
                    <td>{entry.matter?.name || 'Unassigned'}</td>
                    <td>${parseFloat(entry.amount).toFixed(2)}</td>
                    <td>
                      <button onClick={() => handleApprove(entry.id)} className="btn btn-success" style={{ marginRight: '0.5rem' }}>
                        Approve
                      </button>
                      <button onClick={() => handleReject(entry.id)} className="btn btn-danger">
                        Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        <h2 style={{ marginTop: '2rem' }}>Approved Time Entries</h2>
        {timeEntries.length === 0 ? (
          <div className="card"><p>No approved time entries yet.</p></div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Duration</th>
                <th>Matter</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {timeEntries.map((entry) => (
                <tr key={entry.id}>
                  <td>{new Date(entry.date).toLocaleDateString()}</td>
                  <td>{entry.description}</td>
                  <td>{(entry.duration / 60).toFixed(2)}h</td>
                  <td>{entry.matter?.name || '-'}</td>
                  <td>${parseFloat(entry.amount).toFixed(2)}</td>
                  <td>{entry.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

export default TimeEntries;
