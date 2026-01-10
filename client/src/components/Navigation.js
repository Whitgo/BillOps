import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function Navigation() {
  const { user, logout } = useAuth();

  return (
    <nav className="nav">
      <h1>BillOps</h1>
      <div className="nav-links">
        <Link to="/">Dashboard</Link>
        <Link to="/clients">Clients</Link>
        <Link to="/matters">Matters</Link>
        <Link to="/time-entries">Time Entries</Link>
        <Link to="/invoices">Invoices</Link>
        <Link to="/integrations">Integrations</Link>
        <button onClick={logout} className="btn btn-secondary">
          Logout
        </button>
      </div>
    </nav>
  );
}

export default Navigation;
