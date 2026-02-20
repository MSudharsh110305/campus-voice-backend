import React from 'react';
import { useAuth } from '../../../context/AuthContext';
import { Card, EliteButton } from '../../../components/UI';
import AuthoritySidebar from '../components/AuthoritySidebar';
import AuthorityHeader from '../components/AuthorityHeader';
import { User, Mail, Shield, LogOut } from 'lucide-react';

export default function AuthorityProfile() {
    const { user, logout } = useAuth();

    const handleLogout = () => {
        if (window.confirm('Are you sure you want to logout?')) {
            logout();
        }
    };

    return (
        <div className="flex min-h-screen bg-srec-background">
            <AuthoritySidebar className="hidden md:flex fixed inset-y-0 left-0 z-10" />

            <div className="flex-1 md:ml-64 flex flex-col min-w-0 transition-all duration-300">
                <AuthorityHeader />

                <main className="flex-1 p-6 sm:p-8 overflow-y-auto">
                    <h1 className="text-2xl font-bold text-gray-900 tracking-tight mb-8">My Profile</h1>

                    <div className="max-w-2xl mx-auto">
                        <Card className="p-8 border-gray-100 shadow-sm relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-r from-srec-primary to-srec-primaryHover opacity-10"></div>

                            <div className="relative flex flex-col items-center text-center -mt-4 mb-8">
                                <div className="w-24 h-24 bg-white rounded-full p-2 shadow-md mb-4 border border-gray-100">
                                    <div className="w-full h-full bg-srec-primary/10 rounded-full flex items-center justify-center text-srec-primary">
                                        <User size={40} />
                                    </div>
                                </div>
                                <h2 className="text-xl font-bold text-gray-900">{user?.name || 'Authority User'}</h2>
                                <p className="text-sm text-gray-500 font-medium">{user?.designation || 'Authority'}</p>
                                <div className="mt-3">
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200">
                                        <Shield size={12} className="mr-1" />
                                        {user?.role}
                                    </span>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="flex items-center p-4 bg-gray-50 rounded-xl border border-gray-100">
                                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center text-gray-400 border border-gray-100 shadow-sm mr-4">
                                        <Mail size={20} />
                                    </div>
                                    <div>
                                        <p className="text-xs text-uppercase tracking-wider text-gray-400 font-semibold">EMAIL ADDRESS</p>
                                        <p className="text-gray-900 font-medium">{user?.email}</p>
                                    </div>
                                </div>

                                <div className="pt-6 border-t border-gray-100">
                                    <EliteButton
                                        variant="danger"
                                        className="w-full justify-center py-3 text-base shadow-lg shadow-red-100 hover:shadow-red-200"
                                        onClick={handleLogout}
                                    >
                                        <LogOut size={18} className="mr-2" />
                                        Logout
                                    </EliteButton>
                                    <p className="text-xs text-center text-gray-400 mt-4">
                                        You will be redirected to the login page.
                                    </p>
                                </div>
                            </div>
                        </Card>
                    </div>
                </main>
            </div>
        </div>
    );
}
