import React, { useState, useEffect } from 'react';
import studentService from '../../../services/student.service';
import { EliteButton } from '../../../components/UI';
import { Bell, Check, Trash2, AlertCircle, MessageSquare, CheckCircle } from 'lucide-react';

export default function AdminNotifications() {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [unreadOnly, setUnreadOnly] = useState(false);

    useEffect(() => {
        fetchNotifications();
    }, [unreadOnly]);

    const fetchNotifications = async () => {
        try {
            setLoading(true);
            const data = await studentService.getNotifications({ unread_only: unreadOnly, limit: 50 });
            setNotifications(data.notifications || []);
        } catch (err) {
            console.error("Failed", err);
        } finally {
            setLoading(false);
        }
    };

    const handleMarkRead = async (id) => {
        try {
            await studentService.markNotificationRead(id);
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
        } catch (e) { }
    };

    const getIcon = (type) => {
        switch (type) {
            case 'escalation': return <AlertCircle className="text-srec-danger" size={20} />;
            case 'complaint_resolved': return <CheckCircle className="text-srec-primary" size={20} />;
            default: return <Bell className="text-srec-primary" size={20} />;
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
                <div className="flex gap-2">
                    <EliteButton variant="outline" size="sm" onClick={() => setUnreadOnly(!unreadOnly)}>
                        {unreadOnly ? 'Show All' : 'Unread Only'}
                    </EliteButton>
                    <EliteButton variant="ghost" size="sm" onClick={fetchNotifications}>Refresh</EliteButton>
                </div>
            </div>

            <div className="space-y-3">
                {loading ? <div className="text-center py-12">Loading...</div> : notifications.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-2xl border border-gray-100">
                        <Bell className="mx-auto text-gray-300 mb-3" size={32} />
                        <p className="text-gray-500">No new notifications</p>
                    </div>
                ) : (
                    notifications.map(n => (
                        <div key={n.id} className={`bg-white p-4 rounded-xl border flex items-start gap-4 ${n.is_read ? 'border-gray-100' : 'border-srec-primary/20 shadow-sm'}`}>
                            <div className={`p-2 rounded-lg ${n.is_read ? 'bg-gray-100' : 'bg-srec-primary/10'}`}>
                                {getIcon(n.notification_type)}
                            </div>
                            <div className="flex-1">
                                <p className={`text-sm ${n.is_read ? 'text-gray-600' : 'text-gray-900 font-medium'}`}>{n.message}</p>
                                <span className="text-xs text-gray-400 mt-1 block">{new Date(n.created_at).toLocaleString()}</span>
                            </div>
                            {!n.is_read && (
                                <button onClick={() => handleMarkRead(n.id)} className="text-srec-primary hover:text-srec-primaryHover p-1">
                                    <Check size={18} />
                                </button>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
