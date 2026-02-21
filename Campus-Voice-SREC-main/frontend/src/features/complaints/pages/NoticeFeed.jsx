import React, { useState, useEffect } from 'react';
import { TopNav } from '../../../components/Navbars';
import BottomNav from '../../../components/BottomNav';
import { Card, Badge, EliteButton, Skeleton } from '../../../components/UI';
import { useAuth } from '../../../context/AuthContext';
import { useNotifications } from '../../../context/NotificationContext';
import studentService from '../../../services/student.service';
import { Megaphone, Calendar, AlertTriangle, Info } from 'lucide-react';

const PRIORITY_STYLES = {
    Low:    'bg-gray-100 text-gray-600',
    Medium: 'bg-blue-50 text-blue-700',
    High:   'bg-orange-50 text-orange-700',
    Urgent: 'bg-red-50 text-red-700 font-bold',
};

const CATEGORY_ICONS = {
    Announcement:   <Megaphone size={16} />,
    Emergency:      <AlertTriangle size={16} className="text-red-500" />,
    'Policy Change': <Info size={16} />,
    Event:          <Calendar size={16} />,
};

export default function NoticeFeed() {
    const { user } = useAuth();
    const { markNoticesSeen } = useNotifications();
    const [notices, setNotices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [skip, setSkip] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [error, setError] = useState(null);
    const LIMIT = 20;

    useEffect(() => {
        fetchNotices(true);
        markNoticesSeen(); // Clear the notice badge when this page is opened
    }, []);

    const fetchNotices = async (reset = false) => {
        try {
            setLoading(true);
            setError(null);
            const currentSkip = reset ? 0 : skip;
            const data = await studentService.getNotices({ skip: currentSkip, limit: LIMIT });

            const list = data?.notices || [];
            if (reset) {
                setNotices(list);
                setSkip(LIMIT);
            } else {
                setNotices(prev => [...prev, ...list]);
                setSkip(prev => prev + LIMIT);
            }
            setHasMore(list.length === LIMIT);
        } catch (err) {
            setError(err.message || 'Failed to load notices');
        } finally {
            setLoading(false);
        }
    };

    const formatAudience = (notice) => {
        const parts = [];
        if (notice.target_gender?.length) parts.push(notice.target_gender.join('/'));
        if (notice.target_stay_types?.length) parts.push(notice.target_stay_types.join('/'));
        if (notice.target_departments?.length) parts.push(notice.target_departments.join(', '));
        if (notice.target_years?.length) parts.push(`Year ${notice.target_years.join(', ')}`);
        return parts.length ? parts.join(' • ') : 'All Students';
    };

    return (
        <div className="min-h-screen bg-srec-background">
            <TopNav />
            <div className="max-w-3xl mx-auto p-4 sm:p-6 pb-24 md:pl-24 transition-all duration-300">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Notice Board</h1>
                        <p className="text-sm text-gray-500 mt-1">Official announcements from campus authorities</p>
                    </div>
                    <EliteButton variant="outline" size="sm" onClick={() => fetchNotices(true)}>
                        Refresh
                    </EliteButton>
                </div>

                {error && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm">
                        {error}
                    </div>
                )}

                <div className="space-y-4">
                    {loading && notices.length === 0 ? (
                        [1, 2, 3].map(i => <Skeleton key={i} className="h-36 rounded-xl" />)
                    ) : notices.length === 0 ? (
                        <Card className="p-12 text-center shadow-neu-flat">
                            <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-300">
                                <Megaphone size={32} />
                            </div>
                            <h3 className="text-lg font-medium text-gray-900">No notices yet</h3>
                            <p className="text-gray-500 mt-2">Check back later for announcements from campus authorities.</p>
                        </Card>
                    ) : (
                        notices.map((notice) => (
                            <div
                                key={notice.id}
                                className={`bg-white rounded-xl border p-5 shadow-sm transition-all hover:shadow-md
                                    ${notice.priority === 'Urgent' ? 'border-red-200 bg-red-50/30' : 'border-gray-100'}`}
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between gap-3 mb-3">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${PRIORITY_STYLES[notice.priority] || 'bg-gray-100 text-gray-600'}`}>
                                            {CATEGORY_ICONS[notice.category] || <Info size={14} />}
                                            {notice.category}
                                        </span>
                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${PRIORITY_STYLES[notice.priority] || 'bg-gray-100 text-gray-600'}`}>
                                            {notice.priority}
                                        </span>
                                    </div>
                                    <span className="text-xs text-gray-400 whitespace-nowrap">
                                        {new Date(notice.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
                                    </span>
                                </div>

                                {/* Title */}
                                <h3 className="text-base font-bold text-gray-900 mb-2">{notice.title}</h3>

                                {/* Content */}
                                <p className="text-sm text-gray-600 leading-relaxed mb-4 whitespace-pre-wrap">{notice.content}</p>

                                {/* Footer */}
                                <div className="flex items-center justify-between flex-wrap gap-2 pt-3 border-t border-gray-100">
                                    <div className="text-xs text-gray-500">
                                        <span className="font-medium">{notice.authority_name || 'Authority'}</span>
                                        {notice.authority_type && (
                                            <span className="text-gray-400"> · {notice.authority_type}</span>
                                        )}
                                    </div>
                                    <div className="text-xs text-gray-400">
                                        Audience: <span className="font-medium text-gray-600">{formatAudience(notice)}</span>
                                    </div>
                                </div>

                                {/* Expiry warning */}
                                {notice.expires_at && new Date(notice.expires_at) < new Date(Date.now() + 24 * 60 * 60 * 1000) && (
                                    <div className="mt-3 text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg">
                                        Expires: {new Date(notice.expires_at).toLocaleDateString()}
                                    </div>
                                )}
                            </div>
                        ))
                    )}

                    {!loading && hasMore && notices.length > 0 && (
                        <div className="flex justify-center pt-2">
                            <EliteButton variant="outline" onClick={() => fetchNotices(false)}>
                                Load More
                            </EliteButton>
                        </div>
                    )}

                    {loading && notices.length > 0 && (
                        <Skeleton className="h-36 rounded-xl" />
                    )}
                </div>
            </div>
            {user?.role === 'Student' && <BottomNav />}
        </div>
    );
}
