/**
 * Dashboard Layout with responsive sidebar and topbar
 */

import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from '@/components/common/Header';
import Sidebar from '@/components/common/Sidebar';
import '@/styles/globals.css';

export default function DashboardLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleOpenMenu = () => setIsSidebarOpen(true);
  const handleCloseMenu = () => setIsSidebarOpen(false);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={handleCloseMenu}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Escape' && handleCloseMenu()}
        />
      )}

      <Sidebar isOpen={isSidebarOpen} onClose={handleCloseMenu} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onMenuClick={handleOpenMenu} />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
