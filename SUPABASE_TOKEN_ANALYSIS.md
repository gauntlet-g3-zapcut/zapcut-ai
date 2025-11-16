# Supabase Token Algorithm Issue - Comprehensive Analysis

## Executive Summary

The application is experiencing a token algorithm mismatch where HS256 tokens are being detected instead of the expected RS256 tokens. After thorough investigation, I've identified the root causes and provide solutions below.

## Root Causes Identified

### 1. **DUPLICATE API FILES** ⚠️ CRITICAL
- **Location**: `frontend/src/services/`
- **Files**: Both `api.js` AND `api.ts` exist
- **Impact**: Module resolution ambiguity - TypeScript/JavaScript bundler may load the wrong file or both
- **Evidence**: 
  - `api.js` has NO token validation (lines 17-23)
  - `api.ts` has comprehensive validation (lines 35-91)
  - All imports use `from "../services/api"` without extension
  - Vite/TypeScript may resolve to either file unpredictably

### 2. **Stale/Corrupted Tokens in localStorage**
- **Issue**: Old tokens with HS256 algorithm stored in browser localStorage
- **Why**: 
  - Tokens created before PKCE flow was configured
  - Tokens from a different Supabase project
  - Corrupted session data
- **Evidence**: Console logs show session being loaded from storage with HS256 token

### 3. **Validation Timing Issue**
- **Problem**: Token validation happens AFTER Supabase client loads session from storage
- **Current Flow**:
  1. Supabase client initializes
  2. Client loads session from localStorage (may contain HS256 token)
  3. Our validation code runs and detects HS256
  4. We clear session, but it's already been loaded
- **Result**: Validation catches the issue but creates a loop

### 4. **Multiple Validation Layers Creating Loops**
- **Locations**:
  - `supabase.ts`: Pre-initialization validation (lines 28-60)
  - `AuthContext.jsx`: Initial session validation (lines 24-34)
  - `AuthContext.jsx`: Auth state change validation (lines 39-49)
  - `api.ts`: Pre-request validation (lines 35-91)
- **Issue**: Each layer clears session, triggering auth state changes, which triggers more validation

## Supabase Best Practices (From Official Docs)

### Token Algorithms
- **Anon Key**: HS256 (this is NORMAL - it's the API key itself)
- **User Access Tokens**: RS256 (ALWAYS - signed by Supabase Auth server)
- **Refresh Tokens**: Random strings (not JWTs)

### PKCE Flow Configuration
According to Supabase docs:
- PKCE flow is recommended for better security
- Should be set via `flowType: 'pkce'` in client config
- Automatically handles token refresh
- More secure than implicit flow

### Token Storage
- Default: localStorage (for client-side apps)
- Should use `storageKey: 'supabase.auth.token'` for consistency
- Auto-refresh should be enabled: `autoRefreshToken: true`

## Current Implementation Analysis

### ✅ What's Correct

1. **Supabase Client Configuration** (`supabase.ts`)
```typescript
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: 'pkce', // ✅ Correct
    storage: typeof window !== 'undefined' ? window.localStorage : undefined,
    storageKey: 'supabase.auth.token', // ✅ Correct
    debug: import.meta.env.DEV
  }
})
```

2. **Backend Token Verification** (`backend/app/api/auth.py`)
- Uses PyJWKClient with JWKS endpoint ✅
- Validates RS256 algorithm ✅
- Checks issuer is from Supabase ✅

### ❌ What's Wrong

1. **Duplicate API Files**
   - `api.js` has no validation
   - `api.ts` has validation
   - Both exist, causing ambiguity

2. **Over-Validation**
   - Too many validation layers
   - Creating infinite loops
   - Should trust Supabase client to handle tokens

3. **Pre-Initialization Validation Issues**
   - Tries to parse localStorage before client exists
   - May not catch all edge cases
   - Runs synchronously which can cause timing issues

## Recommended Solution

### Step 1: Remove Duplicate File
**Delete `frontend/src/services/api.js`** - Keep only `api.ts`

### Step 2: Simplify Validation
Remove validation from:
- ❌ `supabase.ts` pre-initialization (too early, unreliable)
- ❌ `AuthContext.jsx` (creates loops)
- ✅ Keep only in `api.ts` before API requests (single source of truth)

### Step 3: Trust Supabase Client
The Supabase client library handles:
- Token refresh automatically
- Session validation
- Storage management

We should only validate:
- Before sending tokens to our backend API
- When we receive errors from backend

### Step 4: One-Time Cleanup Script
Add a migration script to clear all localStorage on first load after update:

```typescript
// In supabase.ts, after client creation
if (typeof window !== 'undefined') {
  const STORAGE_VERSION = '2' // Increment when changing auth flow
  const currentVersion = localStorage.getItem('supabase.storage.version')
  
  if (currentVersion !== STORAGE_VERSION) {
    // Clear all Supabase-related storage
    Object.keys(localStorage).forEach(key => {
      if (key.includes('supabase') || key.includes('auth')) {
        localStorage.removeItem(key)
      }
    })
    localStorage.setItem('supabase.storage.version', STORAGE_VERSION)
  }
}
```

## Code Snippets - Current Implementation

### Current `api.ts` (CORRECT - Keep This)
```typescript:frontend/src/services/api.ts
async function getAuthToken() {
  let { data: { session }, error } = await supabase.auth.getSession()
  
  if (error || !session) {
    throw new Error("User not authenticated")
  }
  
  // Validate token algorithm
  const tokenAlgorithm = getTokenAlgorithm(session.access_token)
  if (tokenAlgorithm && tokenAlgorithm !== "RS256") {
    // Clear invalid session
    await supabase.auth.signOut()
    // Clear localStorage
    if (typeof window !== 'undefined') {
      Object.keys(localStorage).forEach(key => {
        if (key.includes('supabase') || key.includes('auth')) {
          localStorage.removeItem(key)
        }
      })
    }
    throw new Error(`Invalid token algorithm: ${tokenAlgorithm}. Please log in again.`)
  }
  
  return session.access_token
}
```

### Current `api.js` (WRONG - Delete This)
```javascript:frontend/src/services/api.js
async function getAuthToken() {
  const { data: { session }, error } = await supabase.auth.getSession()
  if (error || !session) {
    throw new Error("User not authenticated")
  }
  return session.access_token // ❌ NO VALIDATION
}
```

### Current `supabase.ts` (SIMPLIFY)
```typescript:frontend/src/services/supabase.ts
// ❌ REMOVE: Pre-initialization validation (lines 10-63)
// This runs too early and is unreliable

// ✅ KEEP: Client configuration
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: 'pkce',
    storage: typeof window !== 'undefined' ? window.localStorage : undefined,
    storageKey: 'supabase.auth.token',
    debug: import.meta.env.DEV
  }
})
```

### Current `AuthContext.jsx` (SIMPLIFY)
```jsx:frontend/src/context/AuthContext.jsx
// ❌ REMOVE: Token validation in useEffect (lines 11-21, 40-48)
// This creates loops and is redundant

// ✅ SIMPLIFY TO:
useEffect(() => {
  // Get initial session
  supabase.auth.getSession().then(({ data: { session } }) => {
    setUser(session?.user ?? null)
    setLoading(false)
  })

  // Listen for auth changes
  const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
    setUser(session?.user ?? null)
    setLoading(false)
  })

  return () => subscription.unsubscribe()
}, [])
```

## Action Plan

1. **Immediate**: Delete `frontend/src/services/api.js`
2. **Immediate**: Remove validation from `supabase.ts` (pre-init)
3. **Immediate**: Remove validation from `AuthContext.jsx`
4. **Keep**: Validation in `api.ts` (single source of truth)
5. **Add**: Storage version migration script
6. **Test**: Clear browser storage and re-login

## Expected Outcome

After fixes:
- No more duplicate API files
- Single validation point (in `api.ts`)
- No validation loops
- Supabase client handles token management
- Users with stale tokens will be prompted to re-login once
- New tokens will always be RS256 (from PKCE flow)

