import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '../src/components/Layout';
import { useAuth } from '../src/contexts/AuthContext';
import { supabase } from '../lib/supabase';

export default function UpdatePassword() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [session, setSession] = useState(null);
  const router = useRouter();
  const { updatePassword } = useAuth();
  
  // Check for active session with reset token
  useEffect(() => {
    const getSession = async () => {
      const { data, error } = await supabase.auth.getSession();
      
      if (data?.session) {
        setSession(data.session);
      } else if (!data?.session) {
        // If no session and we're on the update password page, 
        // the user likely landed here without a valid reset token
        setError('Invalid or expired password reset link. Please request a new one.');
      }
    };
    
    getSession();
  }, []);
  
  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    
    // Validate passwords match
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    // Validate password strength
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    
    try {
      const { error } = await updatePassword(password);
      
      if (error) throw error;
      
      setMessage('Password updated successfully!');
      
      // Clear form
      setPassword('');
      setConfirmPassword('');
      
      // Redirect to login after a delay
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (error) {
      setError(error.message || 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Layout title="Update Password | Austin Multifamily Map">
      <div className="max-w-md mx-auto my-12 p-6 bg-white shadow-md rounded-lg">
        <h1 className="text-2xl font-bold text-center mb-6">Update Password</h1>
        
        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {message && (
          <div className="bg-green-100 text-green-700 p-3 rounded mb-4">
            {message}
          </div>
        )}
        
        {!session && !error ? (
          <div className="text-center py-4">
            <div className="mb-4">Loading...</div>
          </div>
        ) : error && !session ? (
          <div className="text-center py-4">
            <Link href="/reset-password" className="text-blue-600 hover:underline">
              Request a new reset link
            </Link>
          </div>
        ) : (
          <form onSubmit={handleUpdatePassword} className="space-y-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                New Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                Confirm New Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={loading || message}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        )}
        
        {!error && (
          <div className="mt-6 text-center">
            <Link href="/login" className="text-blue-600 hover:underline">
              Back to Login
            </Link>
          </div>
        )}
      </div>
    </Layout>
  );
} 