import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FileText, AlertTriangle, CheckCircle, Bell, User, LogOut, Megaphone } from 'lucide-react';

const AuthoritySidebar = ({ className = '' }) => {
    const location = useLocation();
    const navigate = useNavigate();

    const menuItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/authority-dashboard' },
        { icon: Megaphone, label: 'Notices', path: '/authority-notices' },
        { icon: Bell, label: 'Notifications', path: '/authority-notifications' },
        { icon: User, label: 'Profile', path: '/authority-profile' },
    ];

    return (
        <div className={`w-64 bg-white min-h-screen border-r border-gray-100 shadow-[4px_0_24px_rgba(0,0,0,0.02)] flex flex-col ${className}`}>
            <div className="p-6 border-b border-gray-50">
                <h2 className="text-xl font-bold text-srec-primary tracking-tight">CampusVoice</h2>
                <p className="text-xs text-srec-primaryHover font-medium mt-1 uppercase tracking-wider">Authority Panel</p>
            </div>

            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                {menuItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                        <button
                            key={item.label}
                            onClick={() => navigate(item.path)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${isActive
                                ? 'bg-srec-primary/10 text-srec-primary font-semibold shadow-sm'
                                : 'text-gray-500 hover:bg-gray-50 hover:text-srec-primary'
                                }`}
                        >
                            <item.icon
                                size={20}
                                className={`transition-colors duration-200 ${isActive ? 'text-srec-primary' : 'text-gray-400 group-hover:text-srec-primary'
                                    }`}
                            />
                            <span>{item.label}</span>
                        </button>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-gray-50">
                {/* Logout button handled in header or here? Prompt says "Header... Profile icon", usually logout is in profile menu or bottom of sidebar. 
                     I'll add a logout button here for convenience if needed, but the prompt specified Sidebar sections: Dashboard... Profile. 
                     Let's stick to the list in prompt for now. */}
            </div>
        </div>
    );
};

export default AuthoritySidebar;
