import React from 'react';
import { useAuth } from '../../../context/AuthContext';
import { Link } from 'react-router-dom';
import { Bell, User, LogOut, Search } from 'lucide-react';
import { EliteButton } from '../../../components/UI';

export default function AdminHeader({ onMenuClick }) {
    const { user, logout } = useAuth();

    return (
        <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6 sticky top-0 z-20">
            <div className="flex items-center gap-4">
                <button
                    onClick={onMenuClick}
                    className="md:hidden p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-lg"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                </button>

                {/* Search Bar - Optional per prompt but good for "Enterprise" feel */}
                <div className="hidden md:flex items-center relative">
                    <Search className="absolute left-3 text-gray-400" size={16} />
                    <input
                        type="text"
                        placeholder="Search complaints, users..."
                        className="pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-srec-primary/20 focus:border-srec-primary w-64 transition-all"
                    />
                </div>
            </div>

            <div className="flex items-center gap-3">
                {/* Notification Icon */}
                <button className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-full transition-colors">
                    <Bell size={20} />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-srec-danger rounded-full border border-white"></span>
                </button>

                <div className="h-6 w-px bg-gray-200 mx-1"></div>

                {/* User Profile */}
                <div className="flex items-center gap-3">
                    <div className="text-right hidden sm:block">
                        <div className="text-sm font-semibold text-gray-900">{user?.name || 'Admin'}</div>
                        <div className="text-xs text-srec-primary font-medium">Administrator</div>
                    </div>

                    <div className="relative group">
                        <button className="w-9 h-9 bg-srec-primary/10 text-srec-primary rounded-full flex items-center justify-center border-2 border-white shadow-sm hover:shadow-md transition-shadow">
                            <User size={18} />
                        </button>

                        {/* Dropdown Menu */}
                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.08)] border border-gray-100 py-1 invisible opacity-0 group-hover:visible group-hover:opacity-100 transition-all transform origin-top-right z-50">
                            <div className="px-4 py-3 border-b border-gray-50">
                                <p className="text-sm font-medium text-gray-900 truncate">{user?.email}</p>
                            </div>
                            <Link to="/admin/profile" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                                <User size={16} /> Profile
                            </Link>
                            <button
                                onClick={logout}
                                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-srec-danger hover:bg-red-50 text-left"
                            >
                                <LogOut size={16} /> Sign Out
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
