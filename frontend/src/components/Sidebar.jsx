import { Link, useLocation } from 'react-router-dom';
import { Home, Search, Activity, Tractor, Users, LayoutDashboard, Info, Settings } from 'lucide-react';

export default function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { icon: Home, label: 'Home', path: '/' },
    { icon: LayoutDashboard, label: 'My Dashboard', path: '/dashboard' },
    { icon: Search, label: 'Disease Detection', path: '/disease-detection' },
    { icon: Activity, label: 'Crop Recommendation', path: '/crop-recommendation' },
    { icon: Tractor, label: 'Equipment Rental', path: '/equipment' },
    { icon: Users, label: 'Farm Workforce', path: '/workforce' },
    { icon: Info, label: 'About', path: '/about' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  return (
    <aside className="hidden md:flex flex-col w-64 bg-card border-r border-border h-full">
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-2">
          {menuItems.map((item) => (
            <Link
              key={item.label}
              to={item.path}
              className={`group flex items-center px-2 py-3 text-sm font-medium rounded-md transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary/10 text-primary'
                  : 'text-text-secondary hover:bg-gray-50 hover:text-text-primary'
              }`}
            >
              <item.icon
                className={`mr-3 flex-shrink-0 h-5 w-5 ${
                  location.pathname === item.path
                    ? 'text-primary'
                    : 'text-gray-400 group-hover:text-gray-500'
                }`}
              />
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}
