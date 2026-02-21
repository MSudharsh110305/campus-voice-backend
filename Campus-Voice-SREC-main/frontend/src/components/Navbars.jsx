import React from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Bell, User, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';

export function TopNav() {
  const { user, logout } = useAuth();
  const { unreadCount } = useNotifications();
  const location = useLocation();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'Admin';
  const isStudent = user?.role === 'Student';

  const initials = user?.name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || 'U';

  return (
    <div className="sticky top-0 z-30 shadow-sm border-b border-gray-100 backdrop-blur-sm bg-white/95">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to={isAdmin ? '/admin' : '/'} className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-srec-primaryLight to-srec-primary flex items-center justify-center text-white font-bold shadow-md shadow-srec-primary/20 group-hover:scale-105 transition-transform">
            CV
          </div>
          <span className="font-bold text-gray-900 tracking-tight text-lg group-hover:text-srec-primary transition-colors">CampusVoice</span>
        </Link>
        <nav className="flex items-center gap-2 text-sm font-medium">
          {isAdmin ? (
            <Link to="/admin" className={`text-lg font-semibold ${location.pathname === '/admin' ? 'text-srec-primary' : 'text-gray-500 hover:text-gray-900'}`}>Dashboard</Link>
          ) : isStudent ? (
            <>
              {/* Notification Bell */}
              <button
                onClick={() => navigate('/notifications')}
                className="relative p-2 rounded-full hover:bg-srec-primary/5 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-srec-primary"
                aria-label="Notifications"
              >
                <Bell
                  size={20}
                  className={unreadCount > 0 ? 'text-srec-primary' : 'text-gray-500'}
                />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 min-w-[16px] h-4 px-0.5 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center border border-white leading-none">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Profile Avatar with dropdown */}
              <div className="relative group">
                <button
                  className="w-9 h-9 rounded-full bg-srec-primary text-white text-sm font-bold flex items-center justify-center shadow-sm hover:shadow-md hover:bg-srec-primaryLight transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-srec-primary"
                  aria-label="Profile"
                >
                  {initials}
                </button>
                {/* Dropdown */}
                <div className="absolute right-0 mt-2 w-44 bg-white rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.10)] border border-gray-100 py-1 invisible opacity-0 group-hover:visible group-hover:opacity-100 transition-all duration-150 origin-top-right z-50">
                  <div className="px-4 py-2.5 border-b border-gray-50">
                    <p className="text-xs font-semibold text-gray-900 truncate">{user?.name}</p>
                    <p className="text-[11px] text-gray-400 truncate">{user?.roll_no}</p>
                  </div>
                  <Link to="/profile" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                    <User size={14} /> Profile
                  </Link>
                  <button
                    onClick={() => { logout(); navigate('/login'); }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 text-left"
                  >
                    <LogOut size={14} /> Sign Out
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </nav>
      </div>
    </div>
  );
}

export function AdminSidebar({ children }) {
  return (
    <div className="min-h-screen sm:grid sm:grid-cols-[220px_1fr]">
      <aside className="hidden sm:block border-r border-srec-border p-4">
        <div className="font-semibold text-gray-900 mb-4">Campus Voice</div>
        <nav className="space-y-2 text-sm">
          <Link to="/admin" className="block text-gray-600 hover:text-gray-900">Dashboard</Link>
        </nav>
      </aside>
      <main>{children}</main>
    </div>
  );
}
