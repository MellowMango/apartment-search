import { useState } from 'react';
import Link from 'next/link';
import Layout from '../src/components/Layout';
import { useAuth } from '../src/contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';

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
    <Layout title="Reset Password | Acquire Apartments">
      <div className="container max-w-md mx-auto my-12 px-4">
        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">Reset password</CardTitle>
            <CardDescription className="text-center">
              Enter your email address and we'll send you a reset link
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
            
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                />
              </div>
              
              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </Button>
            </form>
          </CardContent>
          
          <CardFooter className="flex justify-center">
            <Link href="/login" className="text-primary font-medium text-sm hover:underline">
              Back to login
            </Link>
          </CardFooter>
        </Card>
      </div>
    </Layout>
  );
} 