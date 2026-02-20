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
        if (data.notifications.length < LIMIT) {
          setHasMore(false);
        } else {
          setHasMore(true);
        }
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
      case 'escalation': return <AlertCircle className="text-red-500" size={20} />;
      case 'complaint_resolved': return <CheckCircle className="text-green-500" size={20} />;
      case 'comment_added': return <MessageSquare className="text-blue-500" size={20} />;
      default: return <Bell className="text-srec-primary" size={20} />;
    }
  };

  return (
    <div className="min-h-screen bg-srec-background">
      <TopNav />
      <div className="max-w-3xl mx-auto p-4 sm:p-6 pb-24 md:pl-24 transition-all duration-300">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Notifications</h1>
            <p className="text-sm text-gray-500 mt-1">Stay updated on your complaints</p>
          </div>
          <div className="flex gap-2">
            <EliteButton variant="ghost" className="text-xs" onClick={() => setUnreadOnly(!unreadOnly)}>
              {unreadOnly ? 'Show All' : 'Unread Only'}
            </EliteButton>
            <EliteButton variant="primary" className="text-xs" onClick={handleMarkAllRead}>
              Mark All Read
            </EliteButton>
          </div>
        </div>

        <div className="space-y-3">
          {notifications.length === 0 && !loading ? (
            <Card className="p-12 text-center shadow-neu-flat flex flex-col items-center justify-center">
              <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4 text-gray-400">
                <Bell size={32} />
              </div>
              <h3 className="text-lg font-medium text-gray-900">All caught up!</h3>
              <p className="text-gray-500 mt-2 max-w-sm">You have no new notifications.</p>
            </Card>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                className={`p-4 rounded-xl border transition-all duration-200 ${n.is_read ? 'bg-srec-card border-gray-100' : 'bg-white border-srec-primary/20 shadow-sm border-l-4 border-l-srec-primary'}`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-full shrink-0 ${n.is_read ? 'bg-gray-100' : 'bg-srec-primary/10'}`}>
                    {getIcon(n.notification_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">{n.notification_type?.replace(/_/g, ' ')}</span>
                      <span className="text-xs text-gray-400 whitespace-nowrap">{new Date(n.created_at).toLocaleDateString()}</span>
                    </div>
                    <p className={`text-sm ${n.is_read ? 'text-gray-600' : 'text-gray-900 font-medium'}`}>
                      {n.message}
                    </p>
                    {n.complaint_title && (
                      <p className="text-xs text-gray-500 mt-1 pl-2 border-l-2 border-gray-200">
                        Ref: {n.complaint_title}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col gap-1 shrink-0">
                    {!n.is_read && (
                      <button
                        onClick={() => handleMarkRead(n.id)}
                        className="w-9 h-9 flex items-center justify-center rounded-lg bg-green-50 text-green-600 shadow-[4px_4px_12px_rgba(0,0,0,0.05),-4px_-4px_12px_rgba(255,255,255,0.9)] hover:shadow-[inset_2px_2px_6px_rgba(0,0,0,0.05),inset_-2px_-2px_6px_rgba(255,255,255,0.9)] transition-all active:scale-95"
                        title="Mark as read"
                      >
                        <Check size={16} />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(n.id)}
                      className="w-9 h-9 flex items-center justify-center rounded-lg bg-red-50 text-red-500 shadow-[4px_4px_12px_rgba(0,0,0,0.05),-4px_-4px_12px_rgba(255,255,255,0.9)] hover:shadow-[inset_2px_2px_6px_rgba(0,0,0,0.05),inset_-2px_-2px_6px_rgba(255,255,255,0.9)] transition-all active:scale-95 ml-2"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}

          {loading && <div className="py-4 text-center text-gray-400 text-sm">Loading notifications...</div>}

          {!loading && hasMore && notifications.length > 0 && (
            <EliteButton variant="ghost" className="w-full text-srec-primary" onClick={() => fetchNotifications(false)}>
              Load More
            </EliteButton>
          )}
        </div>

      </div>
      {user?.role === 'Student' && <BottomNav />}
    </div>
  );
}
