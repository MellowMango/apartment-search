import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase, getCurrentUser, signIn, signUp, signOut } from '../../lib/supabase';

interface User {
  id: string;
  email?: string;  // Make email optional to match Supabase's User type
  [key: string]: any;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check for current user when the provider loads
    const loadUser = async () => {
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        console.error('Error loading user:', err);
      } finally {
        setLoading(false);
      }
    };

    // Set up auth state listener
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (session?.user) {
          // Convert Supabase User to our User type
          const userObj: User = {
            id: session.user.id,
            email: session.user.email,
            ...session.user
          };
          setUser(userObj);
        } else {
          setUser(null);
        }
        setLoading(false);
      }
    );

    loadUser();

    // Clean up auth listener on unmount
    return () => {
      authListener?.subscription.unsubscribe();
    };
  }, []);

  const handleSignIn = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      const { data, error } = await signIn(email, password);
      
      if (error) {
        throw error;
      }
      
      setUser(data.user);
    } catch (err: any) {
      setError(err.message || 'Failed to sign in');
      console.error('Error signing in:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      const { data, error } = await signUp(email, password);
      
      if (error) {
        throw error;
      }
      
      // Show confirmation message for email verification if needed
      if (data.user && !data.session) {
        setError('Please check your email for a confirmation link');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to sign up');
      console.error('Error signing up:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    try {
      setLoading(true);
      await signOut();
      setUser(null);
    } catch (err: any) {
      setError(err.message || 'Failed to sign out');
      console.error('Error signing out:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    user,
    loading,
    error,
    signIn: handleSignIn,
    signUp: handleSignUp,
    signOut: handleSignOut,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;