import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    FileText,
    Users,
    Bell,
    Building2,
    TriangleAlert,
    UserCog,
    Shield
} from "lucide-react";

export default function AdminSidebar({ className = "" }) {
    const location = useLocation();
    const menuItems = [
        { name: "Dashboard", path: "/admin", icon: LayoutDashboard },
        { name: "All Complaints", path: "/admin/complaints", icon: FileText },
        { name: "Authorities", path: "/admin/authorities", icon: Users },
        { name: "Escalations", path: "/admin/escalations", icon: TriangleAlert },
        { name: "Departments", path: "/admin/departments", icon: Building2 },
        { name: "Notifications", path: "/admin/notifications", icon: Bell },
        { name: "Profile", path: "/admin/profile", icon: UserCog }
    ];

    return (
        <aside className={`bg-white border-r border-gray-200 shadow-sm w-64 flex-shrink-0 flex flex-col ${className}`}>
            <div className="h-16 flex items-center px-6 border-b border-gray-100">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-srec-primary to-srec-primaryHover flex items-center justify-center text-white font-bold shadow-md mr-3">
                    CV
                </div>
                <div>
                    <h1 className="font-bold text-gray-900 tracking-tight">CampusVoice</h1>
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Admin Panel</p>
                </div>
            </div>

            <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    // Check if active: exact match for admin root, startsWith for others to handle sub-paths if needed
                    const isActive = item.path === '/admin'
                        ? location.pathname === '/admin'
                        : location.pathname.startsWith(item.path);

                    return (
                        <NavLink key={item.name} to={item.path}>
                            <div className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${isActive
                                ? "bg-srec-primary/10 text-srec-primary shadow-inner"
                                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                                }`}>
                                <Icon
                                    size={20}
                                    className={isActive ? "text-srec-primary" : "text-gray-400"}
                                />
                                <span className="text-sm font-medium">{item.name}</span>
                            </div>
                        </NavLink>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-gray-100">
                <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-4 text-white shadow-lg relative overflow-hidden group">
                    <div className="absolute top-0 right-0 -mr-4 -mt-4 w-16 h-16 bg-white opacity-5 rounded-full blur-xl group-hover:scale-150 transition-transform duration-700"></div>
                    <p className="text-xs text-gray-300 mb-1">Signed in as</p>
                    <div className="font-bold truncate">Admin User</div>
                    <div className="text-[10px] bg-white/20 inline-block px-1.5 py-0.5 rounded mt-2">Super Admin</div>
                </div>
            </div>
        </aside>
    );
}
