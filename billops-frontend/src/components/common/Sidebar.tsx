/**
 * Sidebar Navigation Component
 */

import { Link, useLocation } from 'react-router-dom';
import clsx from 'clsx';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const navItems = [
  { label: 'Home', path: '/' },
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Clients', path: '/clients' },
  { label: 'Projects', path: '/projects' },
  { label: 'Invoices', path: '/invoices' },
  { label: 'Time Capture', path: '/time-capture' },
  { label: 'Billing Rules', path: '/billing-rules' },
  { label: 'Users', path: '/users' },
  { label: 'Settings', path: '/settings' },
];

export default function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={clsx(
        'fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 shadow-sm transform transition-transform duration-200 ease-in-out',
        'md:static md:translate-x-0 md:shadow-sm',
        isOpen ? 'translate-x-0' : '-translate-x-full'
      )}
    >
      <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <span className="font-semibold text-gray-900">Navigation</span>
        <button
          type="button"
          onClick={onClose}
          className="text-gray-600 hover:text-gray-900"
          aria-label="Close menu"
        >
          ✕
        </button>
      </div>
      <nav className="p-4 space-y-2">
        {navItems.map(item => (
          <Link
            key={item.path}
            to={item.path}
            onClick={onClose}
            className={`block px-4 py-2 rounded-lg transition-colors ${
              location.pathname === item.path
                ? 'bg-blue-500 text-white font-medium'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
