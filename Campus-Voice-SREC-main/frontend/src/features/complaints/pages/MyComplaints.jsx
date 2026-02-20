import React, { useState, useEffect } from 'react';
import { TopNav } from '../../../components/Navbars';
import BottomNav from '../../../components/BottomNav';
import { useAuth } from '../../../context/AuthContext';
import studentService from '../../../services/student.service';
import ComplaintCard from '../components/ComplaintCard';
import { Select, Button, Skeleton, Card } from '../../../components/UI';
import { STATUSES, PRIORITIES, CATEGORY_LIST } from '../../../utils/constants';
import { Filter, Search, X, SlidersHorizontal, Calendar } from 'lucide-react';
import complaintService from '../../../services/complaint.service';

export default function MyComplaints() {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [skip, setSkip] = useState(0);
  const LIMIT = 20;

  // Advanced Filters State
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    status: 'All',
    priority: 'All',
    category_id: 'All',
    search: '',
    date_from: '',
    date_to: '',
  });

  useEffect(() => {
    fetchComplaints();
  }, [filters, skip]);

  const fetchComplaints = async () => {
    try {
      setLoading(true);

      // Prepare query object
      const query = {
        skip,
        limit: LIMIT,
      };

      if (filters.status !== 'All') query.status = filters.status;
      if (filters.priority !== 'All') query.priority = filters.priority;
      if (filters.category_id !== 'All') query.category_id = filters.category_id;
      if (filters.search) query.search = filters.search;
      if (filters.date_from) query.date_from = filters.date_from;
      if (filters.date_to) query.date_to = filters.date_to;

      // Use advanced filter endpoint
      const data = await complaintService.getAdvancedFilteredComplaints(query);

      if (data && Array.isArray(data.complaints)) {
        setComplaints(data.complaints);
      } else {
        setComplaints([]);
      }
    } catch (error) {
      console.error("Failed to fetch complaints", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (name, val) => {
    setFilters(prev => ({ ...prev, [name]: val }));
    setSkip(0);
  };

  const resetFilters = () => {
    setFilters({
      status: 'All',
      priority: 'All',
      category_id: 'All',
      search: '',
      date_from: '',
      date_to: '',
    });
    setSkip(0);
  };

  return (
    <div className="min-h-screen bg-background">
      <TopNav />
      <main className="max-w-4xl mx-auto px-4 py-8 pb-24">
        <div className="flex flex-col gap-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Your Complaints</h1>
              <p className="text-sm text-gray-500 mt-1">Track and manage your submitted issues</p>
            </div>
            <Button
              variant={showFilters ? 'primary' : 'ghost'}
              className="flex items-center gap-2 rounded-xl shadow-neu-flat border-gray-100"
              onClick={() => setShowFilters(!showFilters)}
            >
              <SlidersHorizontal size={18} />
              <span className="hidden sm:inline">Filters</span>
              {(filters.status !== 'All' || filters.priority !== 'All' || filters.category_id !== 'All' || filters.search || filters.date_from || filters.date_to) && (
                <span className="w-2 h-2 bg-brand rounded-full animate-pulse" />
              )}
            </Button>
          </div>

          {/* Search Bar - Realtime */}
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-brand transition-colors" size={20} />
            <input
              type="text"
              placeholder="Search by ID or description..."
              className="w-full bg-white rounded-2xl border border-gray-100 py-4 pl-12 pr-4 shadow-neu-soft focus:shadow-neu-flat focus:ring-2 focus:ring-brand/20 transition-all outline-none text-gray-700 font-medium"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>

          {/* Advanced Filter Panel */}
          {showFilters && (
            <Card className="p-6 border-brand/10 bg-brand/[0.02] shadow-neu-inset rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Status</label>
                  <Select
                    options={['All', ...STATUSES]}
                    value={filters.status}
                    onChange={(val) => handleFilterChange('status', val)}
                    className="w-full bg-white shadow-sm"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Priority</label>
                  <Select
                    options={['All', ...PRIORITIES]}
                    value={filters.priority}
                    onChange={(val) => handleFilterChange('priority', val)}
                    className="w-full bg-white shadow-sm"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Category</label>
                  <Select
                    options={[
                      { value: 'All', label: 'All Categories' },
                      ...CATEGORY_LIST.map(c => ({ value: c.id, label: c.name }))
                    ]}
                    value={filters.category_id}
                    onChange={(val) => handleFilterChange('category_id', val)}
                    className="w-full bg-white shadow-sm"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Date From</label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                    <input
                      type="date"
                      className="w-full bg-white border border-gray-200 rounded-lg py-2 pl-9 pr-3 text-sm focus:ring-2 focus:ring-brand/20 outline-none"
                      value={filters.date_from}
                      onChange={(e) => handleFilterChange('date_from', e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Date To</label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                    <input
                      type="date"
                      className="w-full bg-white border border-gray-200 rounded-lg py-2 pl-9 pr-3 text-sm focus:ring-2 focus:ring-brand/20 outline-none"
                      value={filters.date_to}
                      onChange={(e) => handleFilterChange('date_to', e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex items-end">
                  <Button
                    variant="ghost"
                    className="w-full h-[40px] text-xs font-bold text-gray-400 hover:text-error hover:bg-error/5 border-dashed rounded-xl"
                    onClick={resetFilters}
                  >
                    <X size={14} className="mr-1" /> Reset Filters
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>

        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-48 rounded-xl" />
            <Skeleton className="h-48 rounded-xl" />
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {complaints.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
                <p className="text-gray-600">No complaints found.</p>
              </div>
            ) : (
              complaints.map((c) => (
                <ComplaintCard
                  key={c.id || c.complaint_id}
                  id={c.id || c.complaint_id}
                  title={c.title}
                  desc={c.description}
                  summary={c.summary}
                  category={c.category}
                  has_image={c.has_image}
                  author={c.is_anonymous ? 'Anonymous' : (c.author || c.student_roll_no)} // Assuming 'my complaints' implies authored by user
                  status={c.status}
                  priority={c.priority}
                  upvotes={c.upvotes}
                  downvotes={c.downvotes}
                  timestamp={c.submitted_at || c.created_at}
                  isOwner={true}
                />
              ))
            )}
          </div>
        )}

        {/* Simple Pagination Controls */}
        <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-100">
          <Button
            variant="ghost"
            className="text-xs font-bold"
            disabled={skip === 0}
            onClick={() => setSkip(Math.max(0, skip - LIMIT))}
          >
            ← Previous
          </Button>
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest bg-gray-50 px-3 py-1 rounded-full border border-gray-100">
            Page {Math.floor(skip / LIMIT) + 1}
          </span>
          <Button
            variant="ghost"
            className="text-xs font-bold"
            disabled={complaints.length < LIMIT}
            onClick={() => setSkip(skip + LIMIT)}
          >
            Next →
          </Button>
        </div>
      </main>

      {user?.role === 'Student' && <BottomNav />}
    </div>
  );
}
