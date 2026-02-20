import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { Badge, Card, Skeleton, RaiseButton, Stat, Button, Select } from '../../../components/UI';
import { TopNav } from '../../../components/Navbars';
import BottomNav from '../../../components/BottomNav';
import ComplaintCard from '../components/ComplaintCard';
import NewComplaintModal from '../components/NewComplaintModal';
import complaintService from '../../../services/complaint.service';
import studentService from '../../../services/student.service';
import { AlertCircle, FileText, SlidersHorizontal, Search, X } from 'lucide-react';
import { STATUSES, PRIORITIES } from '../../../utils/constants';

const initialFeed = [];

export default function StudentHome() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [feed, setFeed] = useState(initialFeed);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('feed'); // feed / mine
  const [showModal, setShowModal] = useState(false);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [myPostsLoading, setMyPostsLoading] = useState(false);

  // Filters for My Posts tab
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    status: 'All',
    priority: 'All',
    category_id: 'All',
    search: '',
  });

  useEffect(() => {
    fetchStats();
    fetchFeed();
  }, [activeTab, filters]);

  const fetchStats = async () => {
    try {
      const data = await studentService.getStats();
      setStats(data);
    } catch (error) {
      console.error("Failed to fetch stats", error);
    }
  };

  const fetchFeed = async () => {
    if (activeTab === 'feed') {
      try {
        setLoading(true);
        setSkip(0);
        setHasMore(true);
        console.log('🔄 Fetching public feed...');

        let data;
        const hasActiveFilters = filters.status !== 'All' || filters.priority !== 'All' || filters.search !== '';

        if (hasActiveFilters) {
          console.log('🔍 Using advanced filters:', filters);
          const apiFilters = {
            skip: 0,
            limit: 20,
            ...(filters.status !== 'All' && { status: filters.status }),
            ...(filters.priority !== 'All' && { priority: filters.priority }),
            ...(filters.search !== '' && { search: filters.search })
          };
          data = await complaintService.getAdvancedFilteredComplaints(apiFilters);
        } else {
          data = await complaintService.getPublicFeed(0, 20);
        }

        console.log('📊 Feed response:', data);

        if (Array.isArray(data)) {
          console.log('✅ Setting feed with array:', data.length, 'items');
          setFeed(data);
          setHasMore(data.length === 20);
        } else if (data && Array.isArray(data.complaints)) {
          console.log('✅ Setting feed with data.complaints:', data.complaints.length, 'items');
          setFeed(data.complaints);
          setHasMore(data.complaints.length === 20);
        } else if (data && Array.isArray(data.data)) {
          console.log('✅ Setting feed with data.data:', data.data.length, 'items');
          setFeed(data.data);
          setHasMore(data.data.length === 20);
        } else {
          console.warn('⚠️ Unexpected data format, setting empty feed:', data);
          setFeed([]);
          setHasMore(false);
        }
        setSkip(20);
      } catch (error) {
        console.error("❌ Failed to load feed:", error);
        // Don't clear the feed on error, keep existing data
      } finally {
        setLoading(false);
      }
    }
  };

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;

    try {
      setLoadingMore(true);
      const data = await complaintService.getPublicFeed(skip, 20);
      console.log("Load More Data:", data);

      let newComplaints = [];
      if (Array.isArray(data)) {
        newComplaints = data;
      } else if (data && Array.isArray(data.complaints)) {
        newComplaints = data.complaints;
      } else if (data && Array.isArray(data.data)) {
        newComplaints = data.data;
      }

      setFeed([...feed, ...newComplaints]);
      setSkip(skip + 20);
      setHasMore(newComplaints.length === 20);
    } catch (error) {
      console.error("Failed to load more:", error);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleNewComplaint = (newComplaint) => {
    // Optimistic update - in real app would refetch
    setFeed([newComplaint, ...feed]);
  };

  return (
    <div className="min-h-screen bg-srec-background">
      <TopNav />
      <div className="max-w-3xl mx-auto p-4 sm:p-6 pb-24 md:pl-24 transition-all duration-300">
        <h2 className="text-2xl font-bold text-gray-900 tracking-tight mb-6">
          Dashboard Overview
        </h2>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Stat label="Total" value={stats?.total_complaints || 0} className="bg-srec-card shadow-neu-flat" />
          <Stat label="Resolved" value={stats?.resolved || 0} color="green" className="bg-srec-card shadow-neu-flat" />
          <Stat label="Pending" value={stats?.in_progress || 0} color="amber" className="bg-srec-card shadow-neu-flat" />
          <Stat label="Votes" value={stats?.total_votes_cast || 0} color="green" className="bg-srec-card shadow-neu-flat" />
        </div>

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 tracking-tight">
            Campus Feed
          </h2>
          <Button
            variant="ghost"
            onClick={() => setShowFilters(!showFilters)}
            className={`gap-2 ${showFilters ? 'bg-srec-primary/10 text-srec-primary' : 'text-gray-500 hover:text-gray-900'}`}
          >
            <SlidersHorizontal size={18} />
            <span className="text-sm">Filters</span>
          </Button>
        </div>

        {showFilters && (
          <Card className="mb-8 p-6 border-srec-primary/10 bg-srec-primary/[0.02] shadow-neu-inset rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                  <input
                    type="text"
                    className="w-full bg-white border border-gray-200 rounded-lg py-2 pl-9 pr-3 text-xs focus:ring-2 focus:ring-srec-primary/20 outline-none"
                    placeholder="Keywords..."
                    value={filters.search}
                    onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Status</label>
                <Select
                  options={['All', ...STATUSES]}
                  value={filters.status}
                  onChange={(val) => setFilters({ ...filters, status: val })}
                  className="w-full bg-white shadow-sm text-xs"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Priority</label>
                <Select
                  options={['All', ...PRIORITIES]}
                  value={filters.priority}
                  onChange={(val) => setFilters({ ...filters, priority: val })}
                  className="w-full bg-white shadow-sm text-xs"
                />
              </div>
              <div className="flex items-end">
                <Button
                  variant="ghost"
                  className="w-full text-[10px] font-bold text-gray-400 hover:text-srec-danger h-[38px]"
                  onClick={() => setFilters({ status: 'All', priority: 'All', category_id: 'All', search: '' })}
                >
                  <X size={12} className="mr-1" /> Reset
                </Button>
              </div>
            </div>
          </Card>
        )}

        {loading && activeTab === 'feed' && (
          <div className="space-y-4">
            <Skeleton className="h-48 rounded-xl" />
            <Skeleton className="h-48 rounded-xl" />
          </div>
        )}

        {myPostsLoading && activeTab === 'mine' && (
          <div className="space-y-4">
            <Skeleton className="h-48 rounded-xl" />
            <Skeleton className="h-48 rounded-xl" />
          </div>
        )}

        <div className="space-y-5">
          {/* Prominent Raise an Issue Button */}
          <RaiseButton
            onClick={() => navigate('/posts')}
            className="w-full"
          >
            <AlertCircle size={20} />
            Raise an Issue
          </RaiseButton>

          {!loading && feed.length === 0 ? (
            <div className="text-center py-16 bg-srec-card rounded-2xl shadow-neu-soft border border-gray-100">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-50 shadow-neu-inset flex items-center justify-center">
                <FileText size={28} className="text-gray-400" />
              </div>
              <p className="text-gray-600 text-lg font-medium">No issues raised yet</p>
              <p className="text-gray-400 text-sm mt-2 max-w-xs mx-auto">
                Be the first to raise a concern! Your voice matters to our campus community.
              </p>
            </div>
          ) : (
            <>
              {feed.map((item) => (
                <ComplaintCard
                  key={item.id || item.complaint_id}
                  id={item.id || item.complaint_id}
                  rephrased_text={item.rephrased_text}
                  summary={item.summary}
                  category={item.category}
                  department_code={item.department_code}
                  has_image={item.has_image}
                  author={item.is_anonymous ? 'Anonymous' : (item.author || item.student_roll_no)}
                  status={item.status}
                  priority={item.priority}
                  upvotes={item.upvotes}
                  downvotes={item.downvotes}
                  timestamp={item.submitted_at}
                />
              ))}

              {hasMore && !loading && (
                <div className="flex justify-center pt-4">
                  <Button
                    onClick={loadMore}
                    disabled={loadingMore}
                    variant="ghost"
                    className="px-6 py-2"
                  >
                    {loadingMore ? 'Loading...' : 'Load More'}
                  </Button>
                </div>
              )}
            </>
          )}
        </div>

      </div>

      <NewComplaintModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSubmit={handleNewComplaint}
      />

      {user?.role === 'Student' && <BottomNav />}
    </div>
  );
}
