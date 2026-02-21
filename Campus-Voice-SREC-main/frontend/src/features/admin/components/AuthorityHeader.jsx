import React, { useState, useRef, useEffect } from 'react';
import { Bell, User, LogOut } from 'lucide-react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';

const PAGE_TITLES = {
  '/authority-dashboard': 'Dashboard',
  '/authority-notices': 'Notices',
  '/authority-notifications': 'Notifications',
  '/authority-profile': 'Profile',
  '/admin': 'Dashboard',
  '/admin/complaints': 'All Complaints',
  '/admin/authorities': 'Manage Authorities',
  '/admin/escalations': 'Escalations',
  '/admin/departments': 'Categories',
  '/admin/notifications': 'Notifications',
  '/admin/profile': 'Profile',
};

const AuthorityHeader = ({ className = '' }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const pageTitle = PAGE_TITLES[location.pathname] || 'Overview';

  const handleBell = () => {
    if (user?.role === 'Admin') {
      navigate('/admin/notifications');
    } else {
      navigate('/authority-notifications');
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Close dropdown on route change
  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  return (
    <header className={`h-16 border-b border-gray-100 bg-white flex items-center justify-between px-8 shadow-sm relative z-30 ${className}`}>
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-gray-900">{pageTitle}</h1>
      </div>

      <div className="flex items-center gap-3">
        {/* Authority Info */}
        <div className="text-right hidden sm:block mr-2">
          <p className="text-sm font-semibold text-gray-900">{user?.name || 'Authority'}</p>
          <p className="text-xs text-srec-primary font-medium">{user?.authority_type || user?.role || 'Authority'}</p>
        </div>

        {/* Notification Bell */}
        <button
          onClick={handleBell}
          className="relative p-2 rounded-full text-gray-400 hover:bg-gray-50 hover:text-srec-primary transition-colors"
          aria-label="Notifications"
        >
          <Bell size={20} />
        </button>

        {/* Profile Icon with click dropdown */}
        <div ref={menuRef} className="relative">
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="w-9 h-9 bg-srec-primary/10 rounded-full flex items-center justify-center border border-srec-primary/20 text-srec-primary shadow-sm hover:bg-srec-primary/20 transition-colors"
            aria-label="Profile menu"
          >
            <User size={18} />
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-[0_8px_30px_rgba(0,0,0,0.12)] border border-gray-100 py-1 z-[100]">
              <div className="px-4 py-3 border-b border-gray-50">
                <p className="text-sm font-semibold text-gray-900 truncate">{user?.name || 'Authority'}</p>
                <p className="text-xs text-srec-primary font-medium">{user?.authority_type || user?.role}</p>
              </div>
              <Link
                to={user?.role === 'Admin' ? '/admin/profile' : '/authority-profile'}
                onClick={() => setMenuOpen(false)}
                className="flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <User size={15} /> Profile
              </Link>
              <button
                onClick={() => { setMenuOpen(false); logout(); navigate('/login'); }}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors text-left"
              >
                <LogOut size={15} /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default AuthorityHeader;
