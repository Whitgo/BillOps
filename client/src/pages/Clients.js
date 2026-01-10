import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import api from '../services/api';

function Clients() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    companyName: '',
    address: '',
  });
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.put(`/clients/${editingId}`, formData);
      } else {
        await api.post('/clients', formData);
      }
      setShowModal(false);
      setFormData({ name: '', email: '', phone: '', companyName: '', address: '' });
      setEditingId(null);
      fetchClients();
    } catch (error) {
      alert('Failed to save client');
    }
  };

  const handleEdit = (client) => {
    setFormData({
      name: client.name,
      email: client.email || '',
      phone: client.phone || '',
      companyName: client.companyName || '',
      address: client.address || '',
    });
    setEditingId(client.id);
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this client?')) {
      try {
        await api.delete(`/clients/${id}`);
        fetchClients();
      } catch (error) {
        alert('Failed to delete client');
      }
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1>Clients</h1>
          <button onClick={() => setShowModal(true)} className="btn btn-primary">
            Add Client
          </button>
        </div>

        {clients.length === 0 ? (
          <div className="card">
            <p>No clients yet. Add your first client to get started!</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Company</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((client) => (
                <tr key={client.id}>
                  <td>{client.name}</td>
                  <td>{client.companyName || '-'}</td>
                  <td>{client.email || '-'}</td>
                  <td>{client.phone || '-'}</td>
                  <td>
                    <button onClick={() => handleEdit(client)} className="btn btn-secondary" style={{ marginRight: '0.5rem' }}>
                      Edit
                    </button>
                    <button onClick={() => handleDelete(client.id)} className="btn btn-danger">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {showModal && (
          <div className="modal" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>{editingId ? 'Edit Client' : 'Add Client'}</h2>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Company Name</label>
                  <input
                    type="text"
                    value={formData.companyName}
                    onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Address</label>
                  <textarea
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  />
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button type="submit" className="btn btn-primary">
                    Save
                  </button>
                  <button type="button" onClick={() => {
                    setShowModal(false);
                    setEditingId(null);
                    setFormData({ name: '', email: '', phone: '', companyName: '', address: '' });
                  }} className="btn btn-secondary">
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default Clients;
