# Fixing Google Authentication in Acquire Application

This document provides instructions for fixing the Google authentication issue in the Acquire application. The main problem was that the Google authentication redirect URL was using an incorrect Supabase project ID.

## 1. Problem Description

When clicking the "Sign in with Google" button, you are redirected to an incorrect URL:
`your-project-id.supabase.co` instead of the actual Supabase project URL `vdrtfnphuixbguedqhox.supabase.co`.

## 2. Solution Steps

### Step 1: Update the Supabase Client Configuration

The Supabase client needs to be configured with the correct authentication options:

```bash
cd /Users/guyma/code/projects/acquire/frontend
```

Edit `lib/supabase.js` to update the Supabase client creation:

```javascript
// Create Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});
```

### Step 2: Update the Google Sign-In Function

Edit `src/contexts/AuthContext.js` to ensure it uses the correct redirect URL:

```javascript
// Login with Google OAuth
const signInWithGoogle = async () => {
  try {
    // Get the correct origin based on the current window
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
```

### Step 3: Configure Supabase OAuth Settings (If Needed)

If the issue persists, check the Supabase OAuth settings in the Supabase dashboard:

1. Log into your Supabase dashboard
2. Navigate to Authentication → Providers → Google
3. Ensure the "Redirect URL" is correctly set to your application URL (e.g., `http://localhost:3002/`)
4. Verify the Google Client ID and Client Secret are correct

## 3. Testing the Fix

1. Start the frontend application:
```bash
cd /Users/guyma/code/projects/acquire/frontend
npm run dev
```

2. Navigate to http://localhost:3002/login
3. Click "Sign in with Google"
4. The authentication flow should now correctly redirect to Google and back to your application

## 4. Troubleshooting

If you still experience issues:

- Check browser console for errors
- Verify that your Google OAuth credentials are configured correctly in both Supabase and Google Cloud Console
- Ensure the redirect URIs in Google Cloud Console match what Supabase expects
- Check if the OAuth site URL is properly configured in Supabase
- Clear browser cookies and try again 