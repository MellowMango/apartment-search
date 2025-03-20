import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { getCurrentUser, signOut } from '../../lib/supabase';

const Header: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const checkUser = async () => {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    };
    
    checkUser();
  }, []);

  const handleSignOut = async () => {
    await signOut();
    setUser(null);
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