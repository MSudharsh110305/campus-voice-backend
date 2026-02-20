import React from 'react';
import { Badge, EliteButton } from '../../../components/UI';
import { format } from 'date-fns';
import { MessageSquare, ThumbsUp, Image as ImageIcon, ArrowUpCircle, MessageCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { VALID_STATUS_TRANSITIONS } from '../../../utils/constants';

const priorityColors = {
    Critical: 'red',
    High: 'orange',
    Medium: 'amber',
    Low: 'gray'
};

const statusColors = {
    Resolved: 'green',
    'In Progress': 'blue',
    Raised: 'yellow',
    Closed: 'gray',
    Spam: 'red'
};

const AuthorityComplaintCard = ({ complaint, onStatusUpdate, onPostUpdate, onEscalate }) => {
    const navigate = useNavigate();
    const validTransitions = VALID_STATUS_TRANSITIONS[complaint.status] || [];
    const canTransition = validTransitions.length > 0;
    const isClosed = complaint.status === 'Closed' || complaint.status === 'Spam';

    return (
        <div
            className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => navigate(`/complaint/${complaint.id}`)}
        >
            {/* Header: Status & Priority */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 flex-wrap">
                    <Badge color={statusColors[complaint.status] || 'gray'}>{complaint.status}</Badge>
                    <Badge color={priorityColors[complaint.priority] || 'gray'}>{complaint.priority}</Badge>
                    <span className="text-xs text-gray-400 font-medium">
                        #{complaint.id?.toString().slice(-6)}
                    </span>
                </div>
                <span className="text-xs text-gray-500 font-medium whitespace-nowrap">
                    {complaint.submitted_at
                        ? format(new Date(complaint.submitted_at), 'MMM dd, h:mm a')
                        : 'Unknown date'}
                </span>
            </div>

            {/* Content */}
            <div className="mb-4">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                        <h3 className="text-base font-bold text-gray-900 mb-1 line-clamp-1">
                            {complaint.category_name || 'General Complaint'}
                        </h3>
                        <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">
                            {complaint.rephrased_text || complaint.original_text}
                        </p>
                        {complaint.student_roll_no && (
                            <p className="text-xs text-gray-400 mt-1">
                                Student: {complaint.student_name || complaint.student_roll_no}
                            </p>
                        )}
                    </div>
                    {complaint.has_image && (
                        <div className="w-14 h-14 rounded-lg bg-gray-50 flex items-center justify-center flex-shrink-0 border border-gray-100">
                            <ImageIcon size={18} className="text-gray-400" />
                        </div>
                    )}
                </div>
            </div>

            {/* Footer: Meta & Actions */}
            <div className="flex items-center justify-between border-t border-gray-50 pt-4 gap-2 flex-wrap">
                <div className="flex items-center gap-3 text-gray-400">
                    <div className="flex items-center gap-1 text-xs font-medium">
                        <ThumbsUp size={13} />
                        <span>{complaint.upvotes || 0}</span>
                    </div>
                    {complaint.vote_count !== undefined && (
                        <div className="flex items-center gap-1 text-xs font-medium">
                            <MessageSquare size={13} />
                            <span>{complaint.vote_count}</span>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-2 flex-wrap justify-end">
                    {/* Status update — only if valid transitions exist */}
                    {canTransition && (
                        <EliteButton
                            size="sm"
                            variant="primary"
                            onClick={(e) => {
                                e.stopPropagation();
                                onStatusUpdate(e, complaint.id, complaint.status);
                            }}
                        >
                            Update Status
                        </EliteButton>
                    )}

                    {/* Post public update — only on active complaints */}
                    {!isClosed && onPostUpdate && (
                        <EliteButton
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                                e.stopPropagation();
                                onPostUpdate(e, complaint.id);
                            }}
                        >
                            <MessageCircle size={13} className="mr-1" />
                            Post Update
                        </EliteButton>
                    )}

                    {/* Escalate — only on active complaints */}
                    {!isClosed && onEscalate && (
                        <EliteButton
                            size="sm"
                            variant="outline"
                            className="text-amber-600 border-amber-200 hover:bg-amber-50"
                            onClick={(e) => {
                                e.stopPropagation();
                                onEscalate(e, complaint.id);
                            }}
                        >
                            <ArrowUpCircle size={13} className="mr-1" />
                            Escalate
                        </EliteButton>
                    )}

                    {/* View Detail */}
                    <EliteButton
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/complaint/${complaint.id}`);
                        }}
                    >
                        View
                    </EliteButton>
                </div>
            </div>
        </div>
    );
};

export default AuthorityComplaintCard;
