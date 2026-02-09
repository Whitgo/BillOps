/**
 * Header Component
 */

import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

interface HeaderProps {
  onMenuClick?: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="flex-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onMenuClick}
            className="md:hidden text-gray-600 hover:text-gray-900"
            aria-label="Open menu"
          >
            ☰
          </button>
          <div>
          <h1 className="text-2xl font-bold text-gray-900">BillOps</h1>
          {user && <p className="text-sm text-gray-500">Welcome, {user.name}</p>}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{user.name}</p>
                <p className="text-xs text-gray-500">{user.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="btn btn-sm btn-outline"
              >
                Logout
              </button>
            </div>
          )}
          {!user && (
            <button
              onClick={() => navigate('/login')}
              className="btn btn-sm btn-primary"
            >
              Login
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
