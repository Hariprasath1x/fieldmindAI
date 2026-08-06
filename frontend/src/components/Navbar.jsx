import { Link, useLocation } from 'react-router-dom';
import { Leaf, Menu } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const { user, loading } = useAuth();

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Disease Detection', path: '/disease-detection' },
    { name: 'Crop Recommendation', path: '/crop-recommendation' },
    { name: 'About', path: '/about' },
  ];

  return (
    <nav className="bg-primary text-white shadow-md z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <Leaf className="h-8 w-8 text-white" />
              <span className="font-bold text-xl tracking-wide">FieldMind</span>
            </Link>
          </div>
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    location.pathname === link.path
                      ? 'bg-secondary text-white'
                      : 'text-green-100 hover:bg-secondary hover:text-white'
                  }`}
                >
                  {link.name}
                </Link>
              ))}
              
              {!user && !loading && (
                <>
                  <Link to="/login" className="px-4 py-2 rounded-md text-sm font-medium border border-white text-white hover:bg-white hover:text-primary transition-colors">
                    Login
                  </Link>
                  <Link to="/register" className="px-4 py-2 rounded-md text-sm font-bold bg-white text-primary hover:bg-gray-100 transition-colors shadow-sm">
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
          <div className="-mr-2 flex md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-green-100 hover:text-white hover:bg-secondary focus:outline-none"
            >
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>
      
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-primary border-t border-secondary">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  location.pathname === link.path
                    ? 'bg-secondary text-white'
                    : 'text-green-100 hover:bg-secondary hover:text-white'
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                {link.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
