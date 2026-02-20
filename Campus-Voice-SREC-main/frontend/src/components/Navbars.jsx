import React, { useState, useEffect } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import studentService from '../services/student.service';

export function TopNav() {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'Admin';
  const isStudent = user?.role === 'Student';
  const [unreadCount, setUnreadCount] = useState(0);

  // Student pages that should show notification bell
  const studentPages = ['/home', '/posts', '/profile', '/notifications'];
  const showNotificationBell = isStudent && studentPages.includes(location.pathname);

  useEffect(() => {
    if (isStudent) {
      fetchUnreadCount();
      // Optional: Poll every minute or listen to socket
      const interval = setInterval(fetchUnreadCount, 60000);
      return () => clearInterval(interval);
    }
  }, [isStudent, location.pathname]); // Refresh on navigation to keep current

  const fetchUnreadCount = async () => {
    try {
      const data = await studentService.getUnreadCount();
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error("Failed to fetch notification count", error);
    }
  };

  return (
    <div className="sticky top-0 z-30 bg-srec-card shadow-sm border-b border-srec-border">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to={isAdmin ? '/admin' : '/'} className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-srec-primaryLight to-srec-primary flex items-center justify-center text-white font-bold shadow-md shadow-srec-primary/20 group-hover:scale-105 transition-transform">
            CV
          </div>
          <span className="font-bold text-gray-900 tracking-tight text-lg group-hover:text-srec-primary transition-colors">CampusVoice</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm font-medium">
          {isAdmin ? (
            <Link to="/admin" className={location.pathname === '/admin' ? 'text-srec-primary' : 'text-gray-500 hover:text-gray-900'}>Dashboard</Link>
          ) : (
            <>
              {showNotificationBell && (
                <button
                  onClick={() => navigate('/notifications')}
                  className="relative p-2 rounded-full text-gray-500 hover:bg-srec-primary/5 hover:text-srec-primary transition-all duration-200"
                  aria-label="Notifications"
                >
                  <Bell size={20} />
                  {unreadCount > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white animate-pulse"></span>
                  )}
                </button>
              )}
            </>
          )}
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
