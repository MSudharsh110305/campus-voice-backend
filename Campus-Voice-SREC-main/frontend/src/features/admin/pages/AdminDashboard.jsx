import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import adminService from '../../../services/admin.service';
import { Card, Select, Skeleton, EliteButton } from '../../../components/UI';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import { AlertTriangle, CheckCircle, Users, FileText, Activity, ArrowUpRight } from 'lucide-react';
import AdminComplaintCard from '../components/AdminComplaintCard';

// Simple stats card for admin dashboard
function StatCard({ label, value, icon: Icon, color = 'blue', sub }) {
  const colorMap = {
    blue:   'bg-blue-50 text-blue-600',
    green:  'bg-green-50 text-green-600',
    red:    'bg-red-50 text-red-600',
    amber:  'bg-amber-50 text-amber-600',
    purple: 'bg-purple-50 text-purple-600',
  };
  return (
    <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-500">{label}</span>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colorMap[color] || colorMap.blue}`}>
          <Icon size={20} />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

const PIE_COLORS = ['#14532D', '#D4AF37', '#22C55E', '#EF4444', '#6366F1'];

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user || user.role !== 'Admin') return;
    loadOverview();
    loadAnalytics();
  }, [user]);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getSystemOverview();
      setOverview(data);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const data = await adminService.getAnalytics(30);
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 rounded-2xl" />)}
        </div>
        <Skeleton className="h-96 rounded-2xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <AlertTriangle className="text-red-500 mb-4" size={48} />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Dashboard Error</h2>
        <p className="text-gray-500 mb-6">{error}</p>
        <EliteButton onClick={loadOverview}>Retry</EliteButton>
      </div>
    );
  }

  // --- Map real API fields ---
  // overview: { total_students, total_authorities, total_complaints,
  //             recent_complaints_7d, complaints_by_status, complaints_by_priority,
  //             complaints_by_category, image_statistics }
  const byStatus = overview?.complaints_by_status || {};
  const byPriority = overview?.complaints_by_priority || {};
  const byCategory = overview?.complaints_by_category || {};

  const totalComplaints = overview?.total_complaints || 0;
  const totalStudents = overview?.total_students || 0;
  const totalAuthorities = overview?.total_authorities || 0;
  const recent7d = overview?.recent_complaints_7d || 0;
  const resolved = byStatus['Resolved'] || 0;
  const criticalCount = byPriority['Critical'] || 0;
  const resolutionRate = totalComplaints > 0
    ? Math.round((resolved / totalComplaints) * 100)
    : 0;

  // analytics: { period_days, total_complaints, resolved_complaints,
  //              resolution_rate_percent, avg_resolution_time_hours, daily_complaints: [{date, count}] }
  // Chart expects array with date + count
  const dailyData = analytics?.daily_complaints || [];

  // Build pie data from complaints_by_category
  const categoryPieData = Object.entries(byCategory).map(([name, value]) => ({ name, value }));

  // Build status bar data
  const statusData = Object.entries(byStatus).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-8 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Executive Dashboard</h1>
          <p className="text-gray-500 mt-1">Real-time overview of system performance and grievance resolution</p>
        </div>
        <EliteButton variant="outline" onClick={loadOverview}>Refresh Data</EliteButton>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Total Complaints"
          value={totalComplaints}
          icon={FileText}
          color="blue"
          sub={`${recent7d} in last 7 days`}
        />
        <StatCard
          label="Resolution Rate"
          value={`${resolutionRate}%`}
          icon={CheckCircle}
          color="green"
          sub={`${resolved} resolved`}
        />
        <StatCard
          label="Critical Issues"
          value={criticalCount}
          icon={AlertTriangle}
          color="red"
          sub={`${byPriority['High'] || 0} High priority`}
        />
        <StatCard
          label="Total Users"
          value={totalStudents + totalAuthorities}
          icon={Users}
          color="purple"
          sub={`${totalStudents} students · ${totalAuthorities} authorities`}
        />
      </div>

      {/* Status breakdown */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        {Object.entries(byStatus).map(([status, count]) => {
          const colors = {
            Raised: 'bg-yellow-50 border-yellow-100 text-yellow-700',
            'In Progress': 'bg-blue-50 border-blue-100 text-blue-700',
            Resolved: 'bg-green-50 border-green-100 text-green-700',
            Closed: 'bg-gray-50 border-gray-100 text-gray-600',
            Spam: 'bg-red-50 border-red-100 text-red-600',
          };
          return (
            <div key={status} className={`rounded-xl border px-4 py-3 text-center ${colors[status] || 'bg-gray-50 border-gray-100 text-gray-600'}`}>
              <p className="text-2xl font-bold">{count}</p>
              <p className="text-xs font-medium mt-0.5">{status}</p>
            </div>
          );
        })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Trend */}
        <Card className="lg:col-span-2 p-6 shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Activity size={20} className="text-srec-primary" />
            Complaint Volume (Last {analytics?.period_days || 30} Days)
          </h3>
          <div className="h-72 w-full">
            {dailyData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dailyData}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#14532D" stopOpacity={0.12} />
                      <stop offset="95%" stopColor="#14532D" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis
                    dataKey="date"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9CA3AF', fontSize: 11 }}
                    tickFormatter={v => v?.slice(5)} // Show MM-DD
                  />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="#14532D"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#colorCount)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-400">No analytics data yet</div>
            )}
          </div>
        </Card>

        {/* Category Pie */}
        <Card className="p-6 shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-900 mb-6">By Category</h3>
          <div className="h-72 w-full">
            {categoryPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryPieData}
                    cx="50%"
                    cy="45%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {categoryPieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend verticalAlign="bottom" height={36} iconSize={10} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-400">No data yet</div>
            )}
          </div>
        </Card>
      </div>

      {/* Analytics Summary Row */}
      {analytics && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-gray-900">{analytics.total_complaints || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Total (last {analytics.period_days}d)</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-green-600">
              {analytics.resolution_rate_percent != null
                ? `${Math.round(analytics.resolution_rate_percent)}%`
                : '—'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Resolution Rate (period)</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-blue-600">
              {analytics.avg_resolution_time_hours != null
                ? `${Math.round(analytics.avg_resolution_time_hours)}h`
                : '—'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Avg Resolution Time</p>
          </div>
        </div>
      )}
    </div>
  );
}
