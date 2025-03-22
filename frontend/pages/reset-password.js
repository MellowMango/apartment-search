import { useState } from 'react';
import Link from 'next/link';
import Layout from '../src/components/Layout';
import { useAuth } from '../src/contexts/AuthContext';

export default function ResetPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const { resetPassword } = useAuth();
  
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);
    
    try {
      const { error } = await resetPassword(email);
      
      if (error) throw error;
      
      setMessage('Password reset link sent to your email.');
      setEmail('');
    } catch (error) {
      setError(error.message || 'Failed to send reset password email.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Layout title="Reset Password | Austin Multifamily Map">
      <div className="max-w-md mx-auto my-12 p-6 bg-white shadow-md rounded-lg">
        <h1 className="text-2xl font-bold text-center mb-6">Reset Password</h1>
        
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
        
        <p className="mb-4 text-gray-600">
          Enter your email address and we'll send you a link to reset your password.
        </p>
        
        <form onSubmit={handleResetPassword} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <Link href="/login" className="text-blue-600 hover:underline">
            Back to Login
          </Link>
        </div>
      </div>
    </Layout>
  );
} 