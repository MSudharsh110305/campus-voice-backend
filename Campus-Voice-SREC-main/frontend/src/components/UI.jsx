import React from 'react';

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-xl shadow-neu-flat border border-brand/5 border-t-2 border-t-brand/20 hover:shadow-neu-hover hover:-translate-y-[1px] transition-all duration-300 ${className}`}>
      {children}
    </div>
  );
}

// Button component moved to ./UI/Button.jsx
export { default as Button } from './UI/Button';

export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse bg-gray-100 rounded ${className}`} />;
}

export function Badge({ children, type = 'default', variant = 'status' }) {
  // Normalize type to title case for matching keys (e.g. "low" -> "Low")
  const normalize = (str) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
  };

  const key = normalize(type);

  // Priority badge styles with pastel gradients
  const priorityStyles = {
    Low: 'bg-gradient-to-r from-priority-low/30 to-priority-low/20 text-green-700 border border-priority-low/40',
    Medium: 'bg-gradient-to-r from-priority-medium/30 to-priority-medium/20 text-amber-700 border border-priority-medium/40',
    High: 'bg-gradient-to-r from-priority-high/30 to-priority-high/20 text-orange-700 border border-priority-high/40',
    Critical: 'bg-gradient-to-r from-priority-critical/30 to-priority-critical/20 text-red-700 border border-priority-critical/40',
  };

  // Status badge styles with pastel gradients  
  const statusStyles = {
    Raised: 'bg-gradient-to-r from-status-raised/30 to-status-raised/20 text-blue-700 border border-status-raised/40',
    Opened: 'bg-gradient-to-r from-status-opened/30 to-status-opened/20 text-teal-700 border border-status-opened/40',
    Reviewed: 'bg-gradient-to-r from-status-reviewed/30 to-status-reviewed/20 text-violet-700 border border-status-reviewed/40',
    Closed: 'bg-gradient-to-r from-status-closed/30 to-status-closed/20 text-gray-600 border border-status-closed/40',
    Pending: 'bg-gradient-to-r from-status-raised/30 to-status-raised/20 text-blue-700 border border-status-raised/40',
    Resolved: 'bg-gradient-to-r from-brand/20 to-brand/10 text-brand-dark border border-brand/30',
    Rejected: 'bg-gradient-to-r from-red-100 to-red-50 text-red-700 border border-red-200',
  };

  // Category badge style
  const categoryStyle = 'bg-gradient-to-r from-brand/15 to-brand/5 text-brand-dark border border-brand/20';

  // Determine which style set to use
  let badgeStyle = 'bg-gray-100 text-gray-700 border border-gray-200';

  if (variant === 'priority' && priorityStyles[key]) {
    badgeStyle = priorityStyles[key];
  } else if (variant === 'status' && statusStyles[key]) {
    badgeStyle = statusStyles[key];
  } else if (variant === 'category') {
    badgeStyle = categoryStyle;
  } else if (statusStyles[key]) {
    badgeStyle = statusStyles[key];
  } else if (priorityStyles[key]) {
    badgeStyle = priorityStyles[key];
  }

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold shadow-sm backdrop-blur-sm ${badgeStyle}`}>
      {children}
    </span>
  );
}

// New Raise Issue Button with coral gradient and 3D press effect
export function RaiseButton({ children, className = '', ...props }) {
  return (
    <button
      className={`
        inline-flex items-center justify-center gap-2
        px-6 py-3.5
        bg-gradient-to-b from-raise-light via-raise to-raise-dark
        text-white font-semibold
        rounded-xl
        shadow-raise-btn
        border-t border-raise-light/50
        transition-all duration-200
        hover:shadow-raise-btn-hover hover:-translate-y-0.5
        active:shadow-raise-pressed active:translate-y-0 active:scale-[0.98]
        focus:outline-none focus:ring-2 focus:ring-raise/50 focus:ring-offset-2
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}

export function Select({ value, onChange, options, placeholder, className = '' }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full appearance-none rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 shadow-neu-light focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand/50 ${className}`}
      >
        {placeholder && <option value="" className="bg-white text-gray-900">{placeholder}</option>}
        {options.map((opt) => {
          const value = typeof opt === 'object' ? opt.value : opt;
          const label = typeof opt === 'object' ? opt.label : opt;
          return (
            <option key={value} value={value} className="bg-white text-gray-900">{label}</option>
          );
        })}
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
}

export function Stat({ label, value, color = 'brand' }) {
  const colorClasses = {
    brand: 'bg-brand/5 text-brand-dark border border-brand/10',
    green: 'bg-brand/5 text-brand-dark border border-brand/10',
    amber: 'bg-accent/5 text-accent-dark border border-accent/10',
    red: 'bg-red-50 text-red-700 border border-red-100',
  }[color] || 'bg-gray-50 text-gray-700';

  return (
    <div className={`rounded-xl ${colorClasses} p-4 shadow-sm`}>
      <div className="text-sm font-medium opacity-80">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
}

// Export new components
export { default as EliteButton } from './UI/EliteButton';
export { default as StatsCard } from './UI/StatsCard';
