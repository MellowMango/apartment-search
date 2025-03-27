import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { cn } from '../../lib/utils';

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
}

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isAdminMenuOpen, setIsAdminMenuOpen] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const router = useRouter();
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
    router.push('/');
  };

  const NavLink: React.FC<NavLinkProps> = ({ href, children, className }) => {
    const isActive = router.pathname === href || router.pathname.startsWith(`${href}/`);
    return (
      <Link href={href} className={cn(
        "transition-colors hover:text-primary", 
        isActive ? "text-primary font-medium" : "text-foreground",
        className
      )}>
        {children}
      </Link>
    );
  };

  return (
    <header className="border-b bg-background sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold text-primary">
              acquire<span className="text-foreground">.</span>
            </span>
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-6 items-center">
            <NavLink href="/">Home</NavLink>
            <NavLink href="/map">Map</NavLink>
            <NavLink href="/about">About</NavLink>
            
            {user ? (
              <>
                <NavLink href="/dashboard">Dashboard</NavLink>

                {/* Admin Dropdown */}
                <div className="relative">
                  <button 
                    onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                    className={cn(
                      "flex items-center transition-colors hover:text-primary",
                      router.pathname.startsWith('/admin') ? "text-primary font-medium" : "text-foreground"
                    )}
                  >
                    Admin
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 ml-1">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </button>
                  
                  {isAdminMenuOpen && (
                    <div className="absolute right-0 mt-2 py-2 w-48 bg-card rounded-md border shadow-lg z-10">
                      <Link 
                        href="/admin/geocoding" 
                        className="block px-4 py-2 text-sm hover:bg-muted"
                        onClick={() => setIsAdminMenuOpen(false)}
                      >
                        Geocoding
                      </Link>
                    </div>
                  )}
                </div>

                {/* User Profile Dropdown */}
                <div className="relative ml-2">
                  <button 
                    onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
                    className="flex items-center space-x-1 bg-primary/10 hover:bg-primary/20 rounded-full py-1.5 px-3 transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-primary">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                    <span className="text-sm font-medium">
                      {user.email?.split('@')[0] || 'Account'}
                    </span>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </button>
                  
                  {isProfileMenuOpen && (
                    <div className="absolute right-0 mt-2 py-2 w-48 bg-card rounded-md border shadow-lg z-10">
                      <div className="px-4 py-2 border-b border-gray-100">
                        <p className="text-sm font-medium">{user.email}</p>
                        <p className="text-xs text-gray-500">Signed in</p>
                      </div>
                      <Link 
                        href="/profile" 
                        className="block px-4 py-2 text-sm hover:bg-muted"
                        onClick={() => setIsProfileMenuOpen(false)}
                      >
                        Profile Settings
                      </Link>
                      <button 
                        onClick={() => {
                          setIsProfileMenuOpen(false);
                          handleSignOut();
                        }}
                        className="w-full text-left block px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <NavLink href="/login" className="py-2">Login</NavLink>
                <Link href="/signup" className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 rounded-md px-3">
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
          <nav className="mt-4 pb-4 space-y-4 md:hidden">
            <NavLink href="/" className="block">Home</NavLink>
            <NavLink href="/map" className="block">Map</NavLink>
            <NavLink href="/about" className="block">About</NavLink>
            
            {user ? (
              <>
                <NavLink href="/dashboard" className="block">Dashboard</NavLink>
                
                {/* Mobile Admin Menu */}
                <div className="mt-2">
                  <div 
                    onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                    className={cn(
                      "flex justify-between items-center cursor-pointer",
                      router.pathname.startsWith('/admin') ? "text-primary font-medium" : "text-foreground"
                    )}
                  >
                    <span>Admin</span>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={`w-4 h-4 transition-transform ${isAdminMenuOpen ? 'rotate-180' : ''}`}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </div>
                  
                  {isAdminMenuOpen && (
                    <div className="ml-4 mt-2 space-y-2">
                      <NavLink href="/admin/geocoding" className="block">Geocoding</NavLink>
                    </div>
                  )}
                </div>
                
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 mr-2 text-primary">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                    <span className="font-medium">{user.email}</span>
                  </div>
                  <Link href="/profile" className="block py-2 text-foreground hover:text-primary">
                    Profile Settings
                  </Link>
                  <button 
                    onClick={handleSignOut}
                    className="mt-2 w-full flex items-center text-red-600 font-medium rounded-md border border-red-200 bg-red-50 hover:bg-red-100 px-4 py-2 transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 mr-2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                    </svg>
                    Sign Out
                  </button>
                </div>
              </>
            ) : (
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Link href="/login" className="flex justify-center items-center border border-gray-300 rounded-md py-2 font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                  Login
                </Link>
                <Link href="/signup" className="flex justify-center items-center bg-primary text-primary-foreground rounded-md py-2 font-medium hover:bg-primary/90 transition-colors">
                  Sign Up
                </Link>
              </div>
            )}
          </nav>
        )}
      </div>
    </header>
  );
};

export default Header;