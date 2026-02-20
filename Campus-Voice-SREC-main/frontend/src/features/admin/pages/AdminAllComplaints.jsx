import React, { useState, useEffect } from 'react';
import complaintService from '../../../services/complaint.service';
import AdminComplaintCard from '../components/AdminComplaintCard';
import { Skeleton, EliteButton, Select } from '../../../components/UI';
import { Filter, X } from 'lucide-react';
import { STATUSES, PRIORITIES } from '../../../utils/constants';

export default function AdminAllComplaints() {
    const [complaints, setComplaints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        status: '',
        priority: '',
        category: ''
    });
    const [skip, setSkip] = useState(0);
    const LIMIT = 20;

    useEffect(() => {
        loadComplaints(true);
    }, [filters]);

    const loadComplaints = async (reset = false) => {
        try {
            setLoading(true);
            const currentSkip = reset ? 0 : skip;

            // Use advanced filter
            const data = await complaintService.getAdvancedFilteredComplaints({
                ...filters,
                limit: LIMIT,
                skip: currentSkip
            });

            if (reset) {
                setComplaints(data.complaints || []);
                setSkip(LIMIT);
            } else {
                setComplaints(prev => [...prev, ...(data.complaints || [])]);
                setSkip(prev => prev + LIMIT);
            }
        } catch (err) {
            console.error("Failed to load complaints");
        } finally {
            setLoading(false);
        }
    };

    const clearFilters = () => setFilters({ status: '', priority: '', category: '' });

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">All Complaints</h1>
                    <p className="text-gray-500">Master list of all student grievances</p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-gray-200 shadow-sm focus-within:ring-2 focus-within:ring-srec-primary/20 focus-within:border-srec-primary">
                        <Filter size={16} className="text-gray-400" />
                        <select
                            className="bg-transparent text-sm focus:outline-none text-gray-700 w-full"
                            value={filters.status}
                            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                        >
                            <option value="">All Statuses</option>
                            {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                    </div>

                    <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-gray-200 shadow-sm focus-within:ring-2 focus-within:ring-srec-primary/20 focus-within:border-srec-primary">
                        <Filter size={16} className="text-gray-400" />
                        <select
                            className="bg-transparent text-sm focus:outline-none text-gray-700 w-full"
                            value={filters.priority}
                            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
                        >
                            <option value="">All Priorities</option>
                            {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                        </select>
                    </div>

                    {(filters.status || filters.priority) && (
                        <button onClick={clearFilters} className="text-sm text-srec-danger hover:text-red-700 flex items-center gap-1">
                            <X size={14} /> Clear
                        </button>
                    )}
                </div>
            </div>

            {loading && complaints.length === 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-40 rounded-2xl" />)}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {complaints.map(c => (
                        <AdminComplaintCard key={c.id} complaint={c} />
                    ))}
                </div>
            )}

            {!loading && complaints.length === 0 && (
                <div className="text-center py-20 bg-white rounded-2xl border border-gray-100">
                    <p className="text-gray-500">No complaints found matching filters.</p>
                </div>
            )}

            {complaints.length > 0 && (
                <div className="flex justify-center mt-8">
                    <EliteButton variant="outline" onClick={() => loadComplaints(false)}>Load More</EliteButton>
                </div>
            )}
        </div>
    );
}
