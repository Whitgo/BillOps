import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import api from '../services/api';

function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const response = await api.get('/invoices');
      setInvoices(response.data);
    } catch (error) {
      console.error('Failed to fetch invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async (id, invoiceNumber) => {
    try {
      const response = await api.get(`/invoices/${id}/pdf`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${invoiceNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      alert('Failed to download PDF');
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
        <h1>Invoices</h1>

        {invoices.length === 0 ? (
          <div className="card"><p>No invoices yet. Create your first invoice!</p></div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Client</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td>{invoice.invoiceNumber}</td>
                  <td>{invoice.client?.name || '-'}</td>
                  <td>{new Date(invoice.issueDate).toLocaleDateString()}</td>
                  <td>${parseFloat(invoice.total).toFixed(2)}</td>
                  <td>
                    <span style={{
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                      backgroundColor: invoice.status === 'paid' ? '#d5f4e6' : '#fadbd8',
                      color: invoice.status === 'paid' ? '#27ae60' : '#e74c3c',
                    }}>
                      {invoice.status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleDownloadPDF(invoice.id, invoice.invoiceNumber)}
                      className="btn btn-primary"
                    >
                      Download PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

export default Invoices;
