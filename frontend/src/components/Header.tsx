import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isAdminMenuOpen, setIsAdminMenuOpen] = useState(false);
  const router = useRouter();
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
    router.push('/');
  };

  return (
    <header className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-3">
        <div className="flex justify-between items-center">
          <Link href="/">
            <div className="text-xl font-bold text-blue-600 cursor-pointer">
              Austin Multifamily Map
            </div>
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-6">
            <Link href="/" className={`hover:text-blue-600 ${router.pathname === '/' ? 'text-blue-600' : ''}`}>
              Home
            </Link>
            <Link href="/map" className={`hover:text-blue-600 ${router.pathname === '/map' ? 'text-blue-600' : ''}`}>
              Map
            </Link>
            <Link href="/about" className={`hover:text-blue-600 ${router.pathname === '/about' ? 'text-blue-600' : ''}`}>
              About
            </Link>
            {user ? (
              <>
                <Link href="/dashboard" className={`hover:text-blue-600 ${router.pathname === '/dashboard' ? 'text-blue-600' : ''}`}>
                  Dashboard
                </Link>

                {/* Admin Dropdown */}
                <div className="relative">
                  <button 
                    onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                    className={`hover:text-blue-600 flex items-center ${router.pathname.startsWith('/admin') ? 'text-blue-600' : ''}`}
                  >
                    Admin
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 ml-1">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </button>
                  
                  {isAdminMenuOpen && (
                    <div className="absolute right-0 mt-2 py-2 w-48 bg-white rounded-md shadow-lg z-10">
                      <Link 
                        href="/admin/geocoding" 
                        className="block px-4 py-2 text-sm hover:bg-gray-100"
                        onClick={() => setIsAdminMenuOpen(false)}
                      >
                        Geocoding
                      </Link>
                    </div>
                  )}
                </div>

                <button 
                  onClick={handleSignOut}
                  className="hover:text-blue-600"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className={`hover:text-blue-600 ${router.pathname === '/login' ? 'text-blue-600' : ''}`}>
                  Login
                </Link>
                <Link href="/signup" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                  Sign Up
                </Link>
              </>
            )}
          </nav>
          
          {/* Mobile menu button */}
          <button 
            className="md:hidden"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
        </div>
        
        {/* Mobile menu */}
        {isMenuOpen && (
          <nav className="mt-3 pb-3 space-y-3 md:hidden">
            <Link href="/" className="block hover:text-blue-600">
              Home
            </Link>
            <Link href="/map" className="block hover:text-blue-600">
              Map
            </Link>
            <Link href="/about" className="block hover:text-blue-600">
              About
            </Link>
            {user ? (
              <>
                <Link href="/dashboard" className="block hover:text-blue-600">
                  Dashboard
                </Link>
                
                {/* Mobile Admin Menu */}
                <div className="mt-2">
                  <div 
                    onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                    className="flex justify-between items-center hover:text-blue-600 cursor-pointer"
                  >
                    <span>Admin</span>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={`w-4 h-4 transition-transform ${isAdminMenuOpen ? 'rotate-180' : ''}`}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </div>
                  
                  {isAdminMenuOpen && (
                    <div className="ml-4 mt-2 space-y-2">
                      <Link href="/admin/geocoding" className="block hover:text-blue-600">
                        Geocoding
                      </Link>
                    </div>
                  )}
                </div>
                
                <button 
                  onClick={handleSignOut}
                  className="block hover:text-blue-600 w-full text-left"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="block hover:text-blue-600">
                  Login
                </Link>
                <Link href="/signup" className="block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-center">
                  Sign Up
                </Link>
              </>
            )}
          </nav>
        )}
      </div>
    </header>
  );
};

export default Header;