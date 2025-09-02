# Vercel Environment Variables Setup

After deploying to Vercel, you need to configure these environment variables in your Vercel dashboard:

## Required Environment Variables

1. **SECRET_KEY**
   - Description: Flask secret key for session management
   - Default: `spice-pilot-secret-key-2024-cooking-adventures`
   - Recommended: Generate a new secure random key for production

2. **GOOGLE_CLIENT_ID** (Optional - for OAuth)
   - Description: Google OAuth client ID
   - Get from: Google Cloud Console
   - Required for: Google login functionality

3. **GOOGLE_CLIENT_SECRET** (Optional - for OAuth)
   - Description: Google OAuth client secret
   - Get from: Google Cloud Console
   - Required for: Google login functionality

4. **FACEBOOK_CLIENT_ID** (Optional - for OAuth)
   - Description: Facebook app ID
   - Get from: Facebook Developers Console
   - Required for: Facebook login functionality

5. **FACEBOOK_CLIENT_SECRET** (Optional - for OAuth)
   - Description: Facebook app secret
   - Get from: Facebook Developers Console
   - Required for: Facebook login functionality

## How to Set Environment Variables in Vercel

1. Go to your Vercel dashboard
2. Select your deployed project
3. Go to Settings → Environment Variables
4. Add each variable with its value
5. Redeploy your application after adding variables

## OAuth Setup Notes

- For Google OAuth: Add your Vercel domain to authorized redirect URIs in Google Cloud Console
- For Facebook OAuth: Add your Vercel domain to valid OAuth redirect URIs in Facebook app settings
- The OAuth functionality will work with placeholder values, but won't enable actual authentication

## Database Note

The SQLite database will be initialized automatically on first deployment. However, for production use, consider migrating to a cloud database service like PlanetScale or Supabase for persistence across deployments.
