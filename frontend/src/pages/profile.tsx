import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { User, Settings, Mail, Phone, MapPin, Building, LogOut, AlertCircle, Check, X } from 'lucide-react';
import { supabase } from '../utils/supabase';

// Define types
type ProfileError = string | null;
type ProfileSuccess = string | null;

interface UserProfile {
  full_name: string;
  phone: string;
  location: string;
  company: string;
}

export default function Profile() {
  const router = useRouter();
  const { user, loading, isAdmin, signOut } = useAuth();
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<ProfileError>(null);
  const [success, setSuccess] = useState<ProfileSuccess>(null);
  const [profile, setProfile] = useState<UserProfile>({
    full_name: '',
    phone: '',
    location: '',
    company: ''
  });

  // Redirect if not logged in
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login?from=profile');
    }
  }, [user, loading, router]);

  // Load user profile data
  useEffect(() => {
    const fetchProfile = async () => {
      if (!user) return;

      try {
        // Initialize with data from auth user object if available
        setProfile({
          full_name: user.user_metadata?.name || '',
          phone: user.user_metadata?.phone || '',
          location: user.user_metadata?.location || '',
          company: user.user_metadata?.company || ''
        });
      } catch (err) {
        console.error('Error loading profile:', err);
        setError('Failed to load profile data');
      }
    };

    if (user) {
      fetchProfile();
    }
  }, [user]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfile(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);

    try {
      // Update the user metadata in Supabase Auth
      const { error } = await supabase.auth.updateUser({
        data: {
          name: profile.full_name,
          phone: profile.phone,
          location: profile.location,
          company: profile.company
        }
      });

      if (error) throw error;

      setSuccess('Profile updated successfully!');
      // Auto-clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('Error updating profile:', err);
      setError(err.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      router.push('/login');
    } catch (err) {
      console.error('Error signing out:', err);
    }
  };

  // Show loading state or redirect if not logged in
  if (loading || !user) {
    return (
      <Layout title="Profile | Acquire Apartments">
        <div className="min-h-[calc(100vh-200px)] flex items-center justify-center py-12 px-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading your profile...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Profile | Acquire Apartments">
      <div className="min-h-[calc(100vh-200px)] py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-background to-muted/30">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center md:text-left">
            <h1 className="text-3xl font-bold tracking-tight mb-2">Your Profile</h1>
            <p className="text-muted-foreground">Manage your account settings and preferences</p>
          </div>
          
          <div className="grid gap-8 md:grid-cols-[250px_1fr]">
            {/* Sidebar Navigation */}
            <div className="space-y-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex flex-col items-center text-center space-y-3 py-4">
                    <div className="relative">
                      <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center">
                        {user.user_metadata?.avatar_url ? (
                          <img 
                            src={user.user_metadata.avatar_url} 
                            alt={profile.full_name || user.email || 'User'}
                            className="h-24 w-24 rounded-full object-cover"
                          />
                        ) : (
                          <User className="h-12 w-12 text-primary" />
                        )}
                      </div>
                      {isAdmin && (
                        <span className="absolute bottom-0 right-0 bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full">
                          Admin
                        </span>
                      )}
                    </div>
                    <div>
                      <h3 className="font-medium">{profile.full_name || 'Your Name'}</h3>
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                    </div>
                  </div>
                  
                  <div className="border-t border-border mt-4 pt-4">
                    <Button 
                      variant="outline" 
                      className="w-full mt-2 text-destructive hover:text-destructive"
                      onClick={handleSignOut}
                    >
                      <LogOut className="h-4 w-4 mr-2" />
                      Sign Out
                    </Button>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-0">
                  <ul className="divide-y divide-border">
                    <li className="px-4 py-3 flex items-center bg-primary/5 font-medium">
                      <User className="h-4 w-4 mr-2 text-primary" />
                      <span>Profile</span>
                    </li>
                    {/* Future menu items */}
                    <li className="px-4 py-3 flex items-center text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors cursor-pointer">
                      <Settings className="h-4 w-4 mr-2" />
                      <span>Account Settings</span>
                    </li>
                    {isAdmin && (
                      <li className="px-4 py-3 flex items-center text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors cursor-pointer" onClick={() => router.push('/admin')}>
                        <Building className="h-4 w-4 mr-2" />
                        <span>Admin Dashboard</span>
                      </li>
                    )}
                  </ul>
                </CardContent>
              </Card>
            </div>
            
            {/* Main Content */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Personal Information</CardTitle>
                  <CardDescription>
                    Update your personal details and contact information
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  {/* Error & Success Messages */}
                  {error && (
                    <Alert variant="destructive" className="mb-6 animate-fadeIn">
                      <AlertCircle className="h-4 w-4 mr-2" />
                      <AlertDescription className="text-sm">{error}</AlertDescription>
                    </Alert>
                  )}
                  
                  {success && (
                    <Alert className="mb-6 animate-fadeIn bg-green-50 border-green-200 text-green-700">
                      <Check className="h-4 w-4 mr-2 text-green-500" />
                      <AlertDescription className="text-sm">{success}</AlertDescription>
                    </Alert>
                  )}
                  
                  <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="space-y-2">
                      <Label htmlFor="full_name" className="text-sm font-medium">
                        Full Name
                      </Label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-muted-foreground">
                          <User className="h-4 w-4" />
                        </div>
                        <Input
                          id="full_name"
                          name="full_name"
                          type="text"
                          value={profile.full_name}
                          onChange={handleInputChange}
                          className="pl-10"
                          placeholder="Your full name"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="phone" className="text-sm font-medium">
                        Phone Number
                      </Label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-muted-foreground">
                          <Phone className="h-4 w-4" />
                        </div>
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          value={profile.phone}
                          onChange={handleInputChange}
                          className="pl-10"
                          placeholder="Your phone number"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="location" className="text-sm font-medium">
                        Location
                      </Label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-muted-foreground">
                          <MapPin className="h-4 w-4" />
                        </div>
                        <Input
                          id="location"
                          name="location"
                          type="text"
                          value={profile.location}
                          onChange={handleInputChange}
                          className="pl-10"
                          placeholder="City, State"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="company" className="text-sm font-medium">
                        Company
                      </Label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-muted-foreground">
                          <Building className="h-4 w-4" />
                        </div>
                        <Input
                          id="company"
                          name="company"
                          type="text"
                          value={profile.company}
                          onChange={handleInputChange}
                          className="pl-10"
                          placeholder="Your company name"
                        />
                      </div>
                    </div>
                    
                    <div className="pt-3">
                      <Button 
                        type="submit"
                        className="w-full md:w-auto"
                        disabled={saving}
                      >
                        {saving ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Saving...
                          </>
                        ) : 'Save Changes'}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Account Information</CardTitle>
                  <CardDescription>
                    Your account details and email settings
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  <div className="space-y-5">
                    <div className="flex flex-col space-y-1.5">
                      <Label className="text-sm font-medium">Email Address</Label>
                      <div className="flex items-center py-2">
                        <Mail className="h-4 w-4 mr-2 text-muted-foreground" />
                        <span>{user.email}</span>
                      </div>
                    </div>
                    
                    <div className="flex flex-col space-y-1.5">
                      <Label className="text-sm font-medium">Account Created</Label>
                      <div className="flex items-center py-2">
                        <span className="text-muted-foreground">
                          {user.created_at ? new Date(user.created_at).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          }) : 'Unknown'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex flex-col space-y-1.5">
                      <Label className="text-sm font-medium">Account Type</Label>
                      <div className="flex items-center py-2">
                        <span className="px-2 py-1 rounded-full text-xs bg-primary/10 text-primary">
                          {isAdmin ? 'Administrator' : 'Standard User'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="border-t border-border mt-6 pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">Email Preferences</h4>
                        <p className="text-sm text-muted-foreground mt-1">Manage your email notification settings</p>
                      </div>
                      <Button variant="outline" size="sm" disabled>
                        Coming Soon
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-destructive">Danger Zone</CardTitle>
                  <CardDescription>
                    Manage critical account actions
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  <div className="border rounded-lg border-destructive/20 p-4 bg-destructive/5">
                    <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                      <div>
                        <h3 className="font-medium flex items-center">
                          <X className="h-4 w-4 mr-2 text-destructive" />
                          Delete Account
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          This will permanently delete your account and all associated data
                        </p>
                      </div>
                      <Button 
                        variant="destructive" 
                        size="sm"
                        disabled
                        className="self-start md:self-center"
                      >
                        Coming Soon
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
} 