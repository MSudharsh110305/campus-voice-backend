import React, { useState, useEffect } from 'react';
import { TopNav } from '../../../components/Navbars';
import BottomNav from '../../../components/BottomNav';
import { Card, EliteButton, Badge } from '../../../components/UI';
import { useAuth } from '../../../context/AuthContext';
import studentService from '../../../services/student.service';
import { Bell, Check, Trash2, Calendar, AlertCircle, MessageSquare, CheckCircle } from 'lucide-react';

export default function Notifications() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const LIMIT = 20;

  useEffect(() => {
    fetchNotifications(true);
  }, [unreadOnly]);

  const fetchNotifications = async (reset = false) => {
    try {
      setLoading(true);
      const currentSkip = reset ? 0 : skip;
      const data = await studentService.getNotifications({
        skip: currentSkip,
        limit: LIMIT,
        unread_only: unreadOnly
      });

      if (data && Array.isArray(data.notifications)) {
        if (reset) {
          setNotifications(data.notifications);
          setSkip(LIMIT);
        } else {
          setNotifications(prev => [...prev, ...data.notifications]);
          setSkip(prev => prev + LIMIT);
        }
        setHasMore(data.notifications.length >= LIMIT);
      }
    } catch (error) {
      console.error("Failed to fetch notifications", error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await studentService.markNotificationRead(id);
      setNotifications(prev => prev.map(n =>
        n.id === id ? { ...n, is_read: true } : n
      ));
    } catch (error) {
      console.error("Failed to mark read", error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await studentService.deleteNotification(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error("Failed to delete", error);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await studentService.markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error("Failed to mark all read", error);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'escalation': return <AlertCircle className="text-amber-500" size={18} />;
      case 'complaint_resolved': return <CheckCircle className="text-green-500" size={18} />;
      case 'comment_added': return <MessageSquare className="text-blue-500" size={18} />;
      default: return <Bell className="text-srec-primary" size={18} />;
    }
  };

  // Left accent bar color by type
  const getAccentColor = (type) => {
    switch (type) {
      case 'escalation': return 'bg-amber-400';
      case 'complaint_resolved': return 'bg-green-400';
      case 'comment_added': return 'bg-blue-400';
      default: return 'bg-srec-primary';
    }
  };

  return (
    <div className="min-h-screen bg-srec-background">
      <TopNav />
      <div className="animate-fadeIn max-w-3xl mx-auto px-4 pt-4 pb-24 md:pl-24 transition-all duration-300">

        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">Notifications</h1>
            <p className="text-sm text-gray-400 mt-0.5">Updates on your complaints</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              onClick={() => setUnreadOnly(!unreadOnly)}
            >
              {unreadOnly ? 'Show All' : 'Unread only'}
            </button>
            <button
              className="text-sm text-srec-primary hover:underline font-medium transition-colors"
              onClick={handleMarkAllRead}
            >
              Mark all read
            </button>
          </div>
        </div>

        <div className="space-y-2">
          {notifications.length === 0 && !loading ? (
            <div className="py-16 bg-white rounded-2xl border border-gray-100 shadow-sm text-center">
              <div className="w-14 h-14 bg-gray-50 rounded-full flex items-center justify-center mb-3 mx-auto text-gray-400">
                <Bell size={28} />
              </div>
              <h3 className="text-base font-semibold text-gray-900">All caught up!</h3>
              <p className="text-gray-400 text-sm mt-1">No new notifications.</p>
            </div>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                className={`flex items-start gap-0 rounded-xl border overflow-hidden transition-all duration-200 ${
                  n.is_read
                    ? 'bg-white border-gray-100'
                    : 'bg-srec-primary/[0.04] border-srec-primary/15'
                }`}
              >
                {/* Left accent bar */}
                <div className={`w-1 self-stretch flex-shrink-0 ${getAccentColor(n.notification_type)}`} />

                <div className="flex-1 flex items-start gap-3 p-4 min-w-0">
                  <div className={`p-1.5 rounded-full shrink-0 mt-0.5 ${n.is_read ? 'bg-gray-100' : 'bg-white shadow-sm'}`}>
                    {getIcon(n.notification_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm leading-snug ${n.is_read ? 'text-gray-600' : 'text-gray-900 font-medium'}`}>
                      {n.message}
                    </p>
                    {n.complaint_title && (
                      <p className="text-xs text-gray-400 mt-1 truncate">
                        Ref: {n.complaint_title}
                      </p>
                    )}
                  </div>
                </div>

                {/* Right side: timestamp + actions */}
                <div className="flex flex-col items-end gap-2 p-3 shrink-0">
                  <span className="text-xs text-gray-400 whitespace-nowrap">
                    {new Date(n.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex gap-1">
                    {!n.is_read && (
                      <button
                        onClick={() => handleMarkRead(n.id)}
                        className="w-7 h-7 flex items-center justify-center rounded-lg bg-green-50 text-green-600 hover:bg-green-100 transition-all active:scale-95"
                        title="Mark as read"
                      >
                        <Check size={13} />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(n.id)}
                      className="w-7 h-7 flex items-center justify-center rounded-lg bg-red-50 text-red-400 hover:bg-red-100 transition-all active:scale-95"
                      title="Delete"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="py-4 text-center text-gray-400 text-sm">Loading notifications...</div>
          )}

          {!loading && hasMore && notifications.length > 0 && (
            <button
              className="w-full py-2.5 text-sm text-srec-primary font-medium hover:underline transition-colors"
              onClick={() => fetchNotifications(false)}
            >
              Load More
            </button>
          )}
        </div>

      </div>
      {user?.role === 'Student' && <BottomNav />}
    </div>
  );
}
