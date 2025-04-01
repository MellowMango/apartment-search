import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../utils/supabase';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';

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
    <Layout title="Update Password | Acquire Apartments">
      <div className="container max-w-md mx-auto my-12 px-4">
        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">Update password</CardTitle>
            <CardDescription className="text-center">
              Create a new password for your account
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {error && (
              <div className="bg-destructive/15 text-destructive p-3 rounded-md mb-4 text-sm">
                {error}
              </div>
            )}
            
            {message && (
              <div className="bg-green-100 text-green-700 p-3 rounded-md mb-4 text-sm">
                {message}
              </div>
            )}
            
            {!session && !error ? (
              <div className="py-4 text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" role="status">
                  <span className="sr-only">Loading...</span>
                </div>
              </div>
            ) : error && !session ? (
              <div className="flex flex-col items-center justify-center py-4 space-y-4">
                <p className="text-muted-foreground text-sm">Your password reset link is invalid or has expired.</p>
                <Button asChild variant="outline" size="sm">
                  <Link href="/reset-password">Request a new reset link</Link>
                </Button>
              </div>
            ) : (
              <form onSubmit={handleUpdatePassword} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="password">New Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <p className="text-muted-foreground text-xs">Password must be at least 6 characters</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
                
                <Button
                  type="submit"
                  className="w-full"
                  disabled={loading || message}
                >
                  {loading ? 'Updating...' : 'Update Password'}
                </Button>
              </form>
            )}
          </CardContent>
          
          {!error && (
            <CardFooter className="flex justify-center">
              <Link href="/login" className="text-primary font-medium text-sm hover:underline">
                Back to login
              </Link>
            </CardFooter>
          )}
        </Card>
      </div>
    </Layout>
  );
} 