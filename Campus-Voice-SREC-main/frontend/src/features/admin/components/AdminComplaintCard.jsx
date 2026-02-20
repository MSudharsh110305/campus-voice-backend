import React from 'react';
import { format } from 'date-fns';
import { Badge, EliteButton } from '../../../components/UI';
import {
    AlertCircle,
    MessageSquare,
    Clock,
    CheckCircle,
    XCircle,
    User,
    ArrowRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function AdminComplaintCard({ complaint, onAssign, onEscalate, onClose, onSpam }) {
    const navigate = useNavigate();

    const priorityColor = {
        'Critical': 'red',
        'High': 'orange',
        'Medium': 'amber',
        'Low': 'gray'
    };

    const statusColor = {
        'Resolved': 'green',
        'In Progress': 'blue',
        'Closed': 'gray',
        'Spam': 'red',
        'Raised': 'amber'
    };

    return (
        <div
            className="bg-white rounded-2xl p-6 border border-gray-100 hover:shadow-lg transition-all duration-300 group cursor-pointer relative overflow-hidden"
            onClick={() => navigate(`/complaint/${complaint.id}`)}
        >
            {/* Hover Highlight Line */}
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-srec-primary transform scale-y-0 group-hover:scale-y-100 transition-transform duration-300 origin-bottom"></div>

            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                    <Badge color={priorityColor[complaint.priority] || 'gray'}>
                        {complaint.priority}
                    </Badge>
                    <Badge color={statusColor[complaint.status] || 'gray'} variant="outline">
                        {complaint.status}
                    </Badge>
                </div>
                <span className="text-xs text-gray-400 font-mono">#{complaint.id.substring(0, 8)}</span>
            </div>

            <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-1 group-hover:text-srec-primary transition-colors">
                {complaint.title}
            </h3>

            {complaint.ai_summary && (
                <div className="bg-blue-50/50 p-3 rounded-lg mb-3 border border-blue-100">
                    <div className="flex items-center gap-1 text-xs font-semibold text-blue-700 mb-1">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
                        AI Summary
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2 italic">
                        "{complaint.ai_summary}"
                    </p>
                </div>
            )}

            <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
                <div className="flex items-center gap-1">
                    <User size={14} />
                    <span>{complaint.student_name || 'Anonymous'}</span>
                </div>
                <div className="flex items-center gap-1">
                    <Clock size={14} />
                    <span>{format(new Date(complaint.submitted_at), 'MMM dd, h:mm a')}</span>
                </div>
                <div className="flex items-center gap-1">
                    <MessageSquare size={14} />
                    <span>{complaint.comments_count || 0} comments</span>
                </div>
            </div>

            <div className="border-t border-gray-100 pt-4 flex justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                <EliteButton size="sm" variant="outline" onClick={() => navigate(`/complaint/${complaint.id}`)}>
                    View Details
                </EliteButton>

                {/* Quick Actions - Only show if not resolved/closed for cleaner UI */}
                {complaint.status !== 'Resolved' && complaint.status !== 'Closed' && (
                    <>
                        {onAssign && (
                            <EliteButton size="sm" variant="secondary" onClick={() => onAssign(complaint.id)}>
                                Assign
                            </EliteButton>
                        )}
                        {onEscalate && complaint.priority !== 'Critical' && (
                            <EliteButton size="sm" variant="warning" onClick={() => onEscalate(complaint.id)}>
                                Escalate
                            </EliteButton>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
