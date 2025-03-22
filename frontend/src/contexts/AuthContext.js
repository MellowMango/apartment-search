import { createContext, useState, useEffect, useContext } from 'react';
import { supabase } from '../../lib/supabase';

// Create the auth context
export const AuthContext = createContext();

// Create the auth provider component
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for user on initial load
  useEffect(() => {
    // Get current session
    const getInitialSession = async () => {
      try {
        setLoading(true);
        
        // Get current user
        const { data: { user: currentUser }, error } = await supabase.auth.getUser();
        
        if (error) {
          throw error;
        }
        
        setUser(currentUser);
      } catch (error) {
        console.error('Error getting initial session:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };
    
    getInitialSession();
    
    // Set up auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
      setLoading(false);
    });
    
    // Clean up subscription on unmount
    return () => {
      subscription?.unsubscribe();
    };
  }, []);
  
  // Login with email and password
  const signInWithEmail = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) {
        throw error;
      }
      
      return { data, error: null };
    } catch (error) {
      console.error('Error signing in:', error);
      return { data: null, error };
    }
  };
  
  // Login with Google OAuth
  const signInWithGoogle = async () => {
    try {
      // Get the correct origin based on Supabase URL, not the current window location
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
      const appUrl = window.location.origin;
      
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${appUrl}/`
        }
      });
      
      if (error) {
        throw error;
      }
      
      return { data, error: null };
    } catch (error) {
      console.error('Error signing in with Google:', error);
      return { data: null, error };
    }
  };
  
  // Sign up with email and password
  const signUpWithEmail = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password
      });
      
      if (error) {
        throw error;
      }
      
      return { data, error: null };
    } catch (error) {
      console.error('Error signing up:', error);
      return { data: null, error };
    }
  };
  
  // Sign out
  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      
      if (error) {
        throw error;
      }
      
      return { error: null };
    } catch (error) {
      console.error('Error signing out:', error);
      return { error };
    }
  };
  
  // Reset password
  const resetPassword = async (email) => {
    try {
      const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/update-password`,
      });
      
      if (error) {
        throw error;
      }
      
      return { data, error: null };
    } catch (error) {
      console.error('Error resetting password:', error);
      return { data: null, error };
    }
  };
  
  // Update password
  const updatePassword = async (password) => {
    try {
      const { data, error } = await supabase.auth.updateUser({
        password
      });
      
      if (error) {
        throw error;
      }
      
      return { data, error: null };
    } catch (error) {
      console.error('Error updating password:', error);
      return { data: null, error };
    }
  };
  
  // Check if user is admin
  const isAdmin = !!user;  // In a real app you would check a role or permission claim
  
  // Create the context value object
  const value = {
    user,
    loading,
    error,
    signInWithEmail,
    signInWithGoogle,
    signUpWithEmail,
    signOut,
    resetPassword,
    updatePassword,
    isAdmin
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Create a hook for using the auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 