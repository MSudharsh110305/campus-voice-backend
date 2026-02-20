import React, { useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Home, FileText, User, Megaphone } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function BottomNav() {
  const location = useLocation();
  const { user } = useAuth();

  // Only show for student users, not admin
  if (!user || user.role === 'Admin') return null;

  const navItems = [
    {
      path: '/home',
      label: 'Home',
      icon: Home,
      routes: ['/home']
    },
    {
      path: '/posts',
      label: 'Posts',
      icon: FileText,
      routes: ['/posts']
    },
    {
      path: '/notices',
      label: 'Notices',
      icon: Megaphone,
      routes: ['/notices']
    },
    {
      path: '/profile',
      label: 'Profile',
      icon: User,
      routes: ['/profile']
    },
  ];

  // Save last visited tab to localStorage
  useEffect(() => {
    const match = navItems.find((item) =>
      item.routes.includes(location.pathname)
    );
    if (match) {
      localStorage.setItem('cv_last_tab', match.path);
    }
  }, [location.pathname]);

  // Check if a nav item is active based on current route
  const isActive = (item) => {
    return item.routes.includes(location.pathname);
  };


  return (
    <>
      {/* Mobile: Bottom navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-30 bg-srec-card border-t border-srec-border shadow-[0_-4px_20px_-2px_rgba(0,0,0,0.05)] md:hidden safe-area-pb">
        <div className="h-16 flex items-center justify-around px-2">
          {navItems.map((item) => {
            const active = isActive(item);
            const IconComponent = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                aria-label={item.label}
                aria-current={active ? 'page' : undefined}
                onClick={() => localStorage.setItem('cv_last_tab', item.path)}
                className={`
                  relative flex flex-col items-center justify-center flex-1 py-1 
                  transition-all duration-200
                  ${active
                    ? 'text-srec-primary'
                    : 'text-gray-400 hover:text-gray-600'
                  }
                `}
              >
                <div className="relative flex flex-col items-center justify-center gap-1">
                  <div className={`
                    relative p-1.5 rounded-xl transition-all duration-300
                    ${active
                      ? 'bg-srec-primary/10 -translate-y-1'
                      : ''
                    }
                  `}>
                    <IconComponent
                      size={24}
                      strokeWidth={active ? 2.5 : 2}
                      className={active ? 'text-srec-primary drop-shadow-sm' : ''}
                    />
                  </div>
                  <span className={`
                    text-[10px] font-semibold transition-colors
                    ${active
                      ? 'text-srec-primary'
                      : 'text-gray-400'
                    }
                  `}>
                    {item.label}
                  </span>
                </div>
              </NavLink>
            );
          })}
        </div>
        {/* Safe area for devices with home indicator */}
        <div className="h-[env(safe-area-inset-bottom,0px)] bg-srec-card" />
      </nav>

      {/* Desktop: Left sidebar */}
      <nav className="hidden md:flex fixed left-0 top-16 bottom-0 z-20 w-20 flex-col items-center bg-srec-card border-r border-srec-border pt-6 shadow-sm">
        {navItems.map((item) => {
          const active = isActive(item);
          const IconComponent = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              aria-label={item.label}
              aria-current={active ? 'page' : undefined}
              onClick={() => localStorage.setItem('cv_last_tab', item.path)}
              className={`
                group my-3 w-12 h-12 flex items-center justify-center rounded-xl transition-all duration-200
                ${active
                  ? 'bg-srec-primary/10 text-srec-primary shadow-inner'
                  : 'text-gray-400 hover:bg-gray-50 hover:text-gray-600'
                }
              `}
            >
              <IconComponent
                size={24}
                strokeWidth={active ? 2.5 : 2}
                className={active ? 'text-srec-primary' : ''}
              />
              <span className="sr-only">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </>
  );
}
