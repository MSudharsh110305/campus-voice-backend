import React, { useState, useEffect } from 'react';
import complaintService from '../../../services/complaint.service';
import AdminComplaintCard from '../components/AdminComplaintCard';
import { Skeleton, EliteButton } from '../../../components/UI';
import { AlertTriangle, CheckCircle } from 'lucide-react';

export default function AdminEscalations() {
    const [complaints, setComplaints] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadEscalations();
    }, []);

    const loadEscalations = async () => {
        try {
            setLoading(true);
            // Fetching all critical/high priority active complaints as escalations
            const data = await complaintService.getAdvancedFilteredComplaints({ priority: 'Critical', status: 'In Progress' });
            setComplaints(data.complaints || []);
        } catch (err) {
            console.error("Failed to load escalations");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="space-y-4">{[1, 2, 3].map(i => <Skeleton key={i} className="h-32 rounded-xl" />)}</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-red-100 text-srec-danger rounded-lg">
                    <AlertTriangle size={24} />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Escalations</h1>
                    <p className="text-srec-danger font-medium text-sm">Critical issues requiring immediate attention</p>
                </div>
            </div>

            {complaints.length === 0 ? (
                <div className="text-center py-20 bg-white rounded-2xl border border-gray-100">
                    <div className="w-16 h-16 bg-srec-primary/10 rounded-full flex items-center justify-center mx-auto mb-4 text-srec-primary">
                        <CheckCircle size={32} />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900">No Escalations</h3>
                    <p className="text-gray-500">System is running smoothly.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {complaints.map(c => (
                        <AdminComplaintCard key={c.id} complaint={c} />
                    ))}
                </div>
            )}
        </div>
    );
}
