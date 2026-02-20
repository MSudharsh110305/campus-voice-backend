import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import authorityService from '../../../services/authority.service';
import { Card, EliteButton, Select } from '../../../components/UI';
import StatsCard from '../../../components/UI/StatsCard';
import AuthoritySidebar from '../components/AuthoritySidebar';
import AuthorityHeader from '../components/AuthorityHeader';
import AuthorityComplaintCard from '../components/AuthorityComplaintCard';
import { STATUSES, VALID_STATUS_TRANSITIONS, REASON_REQUIRED_STATUSES } from '../../../utils/constants';
import { LayoutDashboard, CheckCircle, Clock, AlertCircle, X } from 'lucide-react';

// Generic modal backdrop
function Modal({ open, onClose, title, children }) {
    if (!open) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <Card className="w-full max-w-md p-6 bg-white shadow-xl border-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-gray-900">{title}</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                        <X size={20} />
                    </button>
                </div>
                {children}
            </Card>
        </div>
    );
}

export default function AuthorityDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [dashboard, setDashboard] = useState(null);
    const [complaints, setComplaints] = useState([]);
    const [statusFilter, setStatusFilter] = useState('All');
    const [error, setError] = useState(null);

    // Status update modal
    const [statusModal, setStatusModal] = useState({ open: false, complaintId: null, currentStatus: null });
    const [newStatus, setNewStatus] = useState('');
    const [statusReason, setStatusReason] = useState('');
    const [statusSubmitting, setStatusSubmitting] = useState(false);

    // Post update modal
    const [postUpdateModal, setPostUpdateModal] = useState({ open: false, complaintId: null });
    const [updateTitle, setUpdateTitle] = useState('');
    const [updateContent, setUpdateContent] = useState('');
    const [postUpdateSubmitting, setPostUpdateSubmitting] = useState(false);

    // Escalate modal
    const [escalateModal, setEscalateModal] = useState({ open: false, complaintId: null });
    const [escalateReason, setEscalateReason] = useState('');
    const [escalateSubmitting, setEscalateSubmitting] = useState(false);

    // Feedback messages
    const [feedback, setFeedback] = useState({ type: '', message: '' });

    useEffect(() => {
        if (!user) {
            navigate('/authority-login');
            return;
        }
        if (user.role !== 'Authority' && user.role !== 'Admin') {
            setError('You do not have permission to access this dashboard');
            return;
        }
        loadDashboard();
    }, []);

    useEffect(() => {
        if (dashboard) loadComplaints();
    }, [statusFilter]);

    const showFeedback = (type, message) => {
        setFeedback({ type, message });
        setTimeout(() => setFeedback({ type: '', message: '' }), 4000);
    };

    const loadDashboard = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await authorityService.getDashboard();
            setDashboard(data);
            await loadComplaints();
        } catch (err) {
            setError(err.message || 'Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    const loadComplaints = async () => {
        try {
            const filter = statusFilter === 'All' ? null : statusFilter;
            const data = await authorityService.getMyComplaints(0, 50, filter);
            let list = [];
            if (Array.isArray(data)) list = data;
            else if (data?.complaints) list = data.complaints;
            else if (data?.data) list = data.data;
            setComplaints(list);
        } catch (err) {
            console.error('Failed to load complaints:', err);
            setComplaints([]);
        }
    };

    // --- Status Update ---
    const openStatusModal = (e, complaintId, currentStatus) => {
        e.stopPropagation();
        const validNext = VALID_STATUS_TRANSITIONS[currentStatus] || [];
        if (validNext.length === 0) return; // No transitions available
        setStatusModal({ open: true, complaintId, currentStatus });
        setNewStatus(validNext[0]);
        setStatusReason('');
    };

    const handleStatusUpdate = async () => {
        if (!newStatus) return;
        const needsReason = REASON_REQUIRED_STATUSES.includes(newStatus);
        if (needsReason && !statusReason.trim()) {
            showFeedback('error', `A reason is required when marking as "${newStatus}"`);
            return;
        }
        setStatusSubmitting(true);
        try {
            await authorityService.updateComplaintStatus(
                statusModal.complaintId,
                newStatus,
                statusReason.trim() || null
            );
            setStatusModal({ open: false, complaintId: null, currentStatus: null });
            showFeedback('success', `Status updated to "${newStatus}" successfully`);
            await loadComplaints();
            await loadDashboard();
        } catch (err) {
            showFeedback('error', err.message || 'Failed to update status');
        } finally {
            setStatusSubmitting(false);
        }
    };

    // --- Post Update ---
    const openPostUpdateModal = (e, complaintId) => {
        e.stopPropagation();
        setPostUpdateModal({ open: true, complaintId });
        setUpdateTitle('');
        setUpdateContent('');
    };

    const handlePostUpdate = async () => {
        if (!updateTitle.trim() || !updateContent.trim()) {
            showFeedback('error', 'Both title and content are required for a public update');
            return;
        }
        setPostUpdateSubmitting(true);
        try {
            await authorityService.postUpdate(postUpdateModal.complaintId, updateTitle.trim(), updateContent.trim());
            setPostUpdateModal({ open: false, complaintId: null });
            showFeedback('success', 'Public update posted successfully');
        } catch (err) {
            showFeedback('error', err.message || 'Failed to post update');
        } finally {
            setPostUpdateSubmitting(false);
        }
    };

    // --- Escalate ---
    const openEscalateModal = (e, complaintId) => {
        e.stopPropagation();
        setEscalateModal({ open: true, complaintId });
        setEscalateReason('');
    };

    const handleEscalate = async () => {
        if (!escalateReason.trim()) {
            showFeedback('error', 'A reason is required to escalate the complaint');
            return;
        }
        setEscalateSubmitting(true);
        try {
            await authorityService.escalateComplaint(escalateModal.complaintId, escalateReason.trim());
            setEscalateModal({ open: false, complaintId: null });
            showFeedback('success', 'Complaint escalated successfully');
            await loadComplaints();
        } catch (err) {
            showFeedback('error', err.message || 'Failed to escalate complaint');
        } finally {
            setEscalateSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-srec-background flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-srec-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-500 font-medium">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-srec-background flex items-center justify-center">
                <Card className="p-8 max-w-md shadow-lg border-red-100">
                    <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mb-4 mx-auto text-srec-danger">
                        <AlertCircle size={24} />
                    </div>
                    <h2 className="text-xl font-bold text-red-900 mb-2 text-center">Access Denied</h2>
                    <p className="text-gray-600 mb-6 text-center">{error}</p>
                    <EliteButton onClick={loadDashboard} className="w-full justify-center">Retry Connection</EliteButton>
                </Card>
            </div>
        );
    }

    const stats = dashboard?.stats || {};
    const validNextStatuses = statusModal.currentStatus
        ? VALID_STATUS_TRANSITIONS[statusModal.currentStatus] || []
        : [];

    return (
        <div className="flex min-h-screen bg-srec-background">
            <AuthoritySidebar className="hidden md:flex fixed inset-y-0 left-0 z-10" />

            <div className="flex-1 md:ml-64 flex flex-col min-w-0 transition-all duration-300">
                <AuthorityHeader />

                <main className="flex-1 p-6 sm:p-8 overflow-y-auto">

                    {/* Feedback banner */}
                    {feedback.message && (
                        <div className={`mb-4 p-4 rounded-xl text-sm font-medium flex items-center gap-2 ${
                            feedback.type === 'success'
                                ? 'bg-green-50 border border-green-100 text-green-700'
                                : 'bg-red-50 border border-red-100 text-red-600'
                        }`}>
                            {feedback.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                            {feedback.message}
                        </div>
                    )}

                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                        <StatsCard
                            label="Total Assigned"
                            value={stats.total_assigned || 0}
                            icon={LayoutDashboard}
                            color="blue"
                        />
                        <StatsCard
                            label="In Progress"
                            value={stats.in_progress || 0}
                            icon={Clock}
                            color="yellow"
                        />
                        <StatsCard
                            label="Resolved"
                            value={stats.resolved || 0}
                            icon={CheckCircle}
                            color="green"
                        />
                        <StatsCard
                            label="Pending"
                            value={stats.pending || stats.raised || 0}
                            icon={AlertCircle}
                            color="red"
                        />
                    </div>

                    {/* Filter Section */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                        <h2 className="text-xl font-bold text-gray-900 tracking-tight">Assigned Complaints</h2>
                        <div className="flex items-center gap-3">
                            <span className="text-sm text-gray-500 font-medium">Filter by:</span>
                            <Select
                                value={statusFilter}
                                onChange={setStatusFilter}
                                options={[
                                    { value: 'All', label: 'All Statuses' },
                                    ...STATUSES.map(s => ({ value: s, label: s }))
                                ]}
                                className="w-48 bg-white border-gray-200"
                            />
                        </div>
                    </div>

                    {/* Complaints List */}
                    {complaints.length === 0 ? (
                        <div className="bg-white rounded-2xl p-12 text-center border border-gray-100 shadow-sm">
                            <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4 mx-auto text-gray-400">
                                <LayoutDashboard size={28} />
                            </div>
                            <h3 className="text-lg font-bold text-gray-900 mb-2">No complaints found</h3>
                            <p className="text-gray-500 mb-6 max-w-md mx-auto">
                                {statusFilter !== 'All'
                                    ? `There are no complaints with status "${statusFilter}" currently assigned to you.`
                                    : 'You have no complaints assigned at the moment.'}
                            </p>
                            <EliteButton variant="outline" onClick={loadDashboard}>
                                Refresh Dashboard
                            </EliteButton>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {complaints.map(complaint => (
                                <AuthorityComplaintCard
                                    key={complaint.id}
                                    complaint={complaint}
                                    onStatusUpdate={openStatusModal}
                                    onPostUpdate={openPostUpdateModal}
                                    onEscalate={openEscalateModal}
                                />
                            ))}
                        </div>
                    )}
                </main>
            </div>

            {/* Status Update Modal */}
            <Modal
                open={statusModal.open}
                onClose={() => setStatusModal({ open: false, complaintId: null, currentStatus: null })}
                title="Update Complaint Status"
            >
                <div className="space-y-4">
                    <div>
                        <p className="text-sm text-gray-500 mb-3">
                            Current status: <span className="font-semibold text-gray-800">{statusModal.currentStatus}</span>
                        </p>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">New Status *</label>
                        <select
                            className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-srec-primary/30 focus:border-srec-primary"
                            value={newStatus}
                            onChange={e => setNewStatus(e.target.value)}
                        >
                            {validNextStatuses.map(s => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                    </div>

                    {(REASON_REQUIRED_STATUSES.includes(newStatus) || statusReason) && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">
                                Reason {REASON_REQUIRED_STATUSES.includes(newStatus) ? '*' : '(optional)'}
                            </label>
                            <textarea
                                className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-srec-primary/30 focus:border-srec-primary outline-none resize-none bg-gray-50 focus:bg-white"
                                rows={3}
                                placeholder={
                                    newStatus === 'Spam' ? 'Reason for flagging as spam...' :
                                    newStatus === 'Closed' ? 'Reason for closing...' :
                                    'Optional reason for status change...'
                                }
                                value={statusReason}
                                onChange={e => setStatusReason(e.target.value)}
                            />
                        </div>
                    )}

                    {!REASON_REQUIRED_STATUSES.includes(newStatus) && !statusReason && (
                        <p className="text-xs text-gray-400">
                            Optionally provide a reason for this status change.
                            <button className="ml-1 text-srec-primary underline" onClick={() => setStatusReason(' ')}>
                                Add reason
                            </button>
                        </p>
                    )}

                    <div className="flex justify-end gap-3 pt-2">
                        <EliteButton
                            variant="outline"
                            onClick={() => setStatusModal({ open: false, complaintId: null, currentStatus: null })}
                            disabled={statusSubmitting}
                        >
                            Cancel
                        </EliteButton>
                        <EliteButton
                            variant="primary"
                            onClick={handleStatusUpdate}
                            disabled={statusSubmitting}
                            isLoading={statusSubmitting}
                        >
                            {statusSubmitting ? 'Updating...' : 'Update Status'}
                        </EliteButton>
                    </div>
                </div>
            </Modal>

            {/* Post Public Update Modal */}
            <Modal
                open={postUpdateModal.open}
                onClose={() => setPostUpdateModal({ open: false, complaintId: null })}
                title="Post Public Update"
            >
                <div className="space-y-4">
                    <p className="text-sm text-gray-500">
                        This update will be visible to the student and all who can view this complaint.
                    </p>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">Title *</label>
                        <input
                            type="text"
                            className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-srec-primary/30 focus:border-srec-primary"
                            placeholder="Update title (e.g. Investigation started)"
                            value={updateTitle}
                            onChange={e => setUpdateTitle(e.target.value)}
                            maxLength={200}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">Content *</label>
                        <textarea
                            className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-srec-primary/30 focus:border-srec-primary outline-none resize-none bg-gray-50 focus:bg-white"
                            rows={4}
                            placeholder="Describe the update or action taken..."
                            value={updateContent}
                            onChange={e => setUpdateContent(e.target.value)}
                            maxLength={2000}
                        />
                        <p className="text-xs text-gray-400 mt-1">{updateContent.length} / 2000</p>
                    </div>
                    <div className="flex justify-end gap-3 pt-2">
                        <EliteButton
                            variant="outline"
                            onClick={() => setPostUpdateModal({ open: false, complaintId: null })}
                            disabled={postUpdateSubmitting}
                        >
                            Cancel
                        </EliteButton>
                        <EliteButton
                            variant="primary"
                            onClick={handlePostUpdate}
                            disabled={postUpdateSubmitting}
                            isLoading={postUpdateSubmitting}
                        >
                            {postUpdateSubmitting ? 'Posting...' : 'Post Update'}
                        </EliteButton>
                    </div>
                </div>
            </Modal>

            {/* Escalate Modal */}
            <Modal
                open={escalateModal.open}
                onClose={() => setEscalateModal({ open: false, complaintId: null })}
                title="Escalate Complaint"
            >
                <div className="space-y-4">
                    <p className="text-sm text-gray-500">
                        Escalating will forward this complaint to a higher authority. Please provide a reason.
                    </p>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">Reason *</label>
                        <textarea
                            className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-srec-primary/30 focus:border-srec-primary outline-none resize-none bg-gray-50 focus:bg-white"
                            rows={3}
                            placeholder="Why does this need to be escalated? (e.g. requires senior authority approval...)"
                            value={escalateReason}
                            onChange={e => setEscalateReason(e.target.value)}
                        />
                    </div>
                    <div className="flex justify-end gap-3 pt-2">
                        <EliteButton
                            variant="outline"
                            onClick={() => setEscalateModal({ open: false, complaintId: null })}
                            disabled={escalateSubmitting}
                        >
                            Cancel
                        </EliteButton>
                        <EliteButton
                            variant="danger"
                            onClick={handleEscalate}
                            disabled={escalateSubmitting}
                            isLoading={escalateSubmitting}
                        >
                            {escalateSubmitting ? 'Escalating...' : 'Escalate'}
                        </EliteButton>
                    </div>
                </div>
            </Modal>
        </div>
    );
}
