import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import api from '../services/api';

function Matters() {
  const [matters, setMatters] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    clientId: '',
    name: '',
    description: '',
    matterNumber: '',
    hourlyRate: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [mattersRes, clientsRes] = await Promise.all([
        api.get('/matters'),
        api.get('/clients'),
      ]);
      setMatters(mattersRes.data);
      setClients(clientsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/matters', formData);
      setShowModal(false);
      setFormData({ clientId: '', name: '', description: '', matterNumber: '', hourlyRate: '' });
      fetchData();
    } catch (error) {
      alert('Failed to create matter');
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
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem' }}>
          <h1>Matters</h1>
          <button onClick={() => setShowModal(true)} className="btn btn-primary">Add Matter</button>
        </div>

        {matters.length === 0 ? (
          <div className="card"><p>No matters yet. Add your first matter!</p></div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Client</th>
                <th>Matter #</th>
                <th>Hourly Rate</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {matters.map((matter) => (
                <tr key={matter.id}>
                  <td>{matter.name}</td>
                  <td>{matter.client?.name || '-'}</td>
                  <td>{matter.matterNumber || '-'}</td>
                  <td>${matter.hourlyRate}</td>
                  <td>{matter.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {showModal && (
          <div className="modal" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Add Matter</h2>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Client *</label>
                  <select value={formData.clientId} onChange={(e) => setFormData({ ...formData, clientId: e.target.value })} required>
                    <option value="">Select Client</option>
                    {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Name *</label>
                  <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label>Matter Number</label>
                  <input type="text" value={formData.matterNumber} onChange={(e) => setFormData({ ...formData, matterNumber: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Hourly Rate *</label>
                  <input type="number" step="0.01" value={formData.hourlyRate} onChange={(e) => setFormData({ ...formData, hourlyRate: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button type="submit" className="btn btn-primary">Save</button>
                  <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">Cancel</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default Matters;
