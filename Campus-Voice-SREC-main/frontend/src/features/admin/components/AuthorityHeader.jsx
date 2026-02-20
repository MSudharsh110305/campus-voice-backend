import React from 'react';
import { Bell, User } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';

const AuthorityHeader = ({ className = '' }) => {
    const { user } = useAuth();

    return (
        <header className={`h-16 bg-white border-b border-gray-100 flex items-center justify-between px-8 shadow-sm ${className}`}>
            <div className="flex items-center gap-4">
                {/* Breadcrumbs or Page Title could go here */}
                <h1 className="text-lg font-semibold text-gray-800">Overview</h1>
            </div>

            <div className="flex items-center gap-6">
                {/* Authority Info */}
                <div className="text-right hidden sm:block">
                    <p className="text-sm font-semibold text-gray-900">{user?.name || 'Authority Name'}</p>
                    <p className="text-xs text-srec-primary font-medium">{user?.role || 'Authority'}</p>
                </div>

                {/* Notification Bell */}
                <button className="relative p-2 rounded-full text-gray-400 hover:bg-gray-50 hover:text-srec-primary transition-colors">
                    <Bell size={20} />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-srec-danger rounded-full ring-2 ring-white"></span>
                </button>

                {/* Profile Icon */}
                <div className="w-9 h-9 bg-srec-primary/10 rounded-full flex items-center justify-center border border-srec-primary/20 text-srec-primary shadow-sm cursor-pointer hover:shadow-md transition-shadow">
                    <User size={18} />
                </div>
            </div>
        </header>
    );
};

export default AuthorityHeader;
