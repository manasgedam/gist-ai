import { useState, useEffect } from 'react';
import { supabase } from '../supabase';

/**
 * Hook to ensure Supabase session is restored before making API calls.
 * 
 * Prevents race condition where API calls fire before session restoration
 * completes on page reload, causing "Missing Authorization header" errors.
 * 
 * Waits for BOTH:
 * - Initial session check via getSession()
 * - Auth state change listener to fire (ensures session fully restored)
 * 
 * Usage:
 * ```tsx
 * const { isAuthReady, session, isAuthenticated } = useAuthReady();
 * 
 * if (!isAuthReady) {
 *   return <div>Loading...</div>;
 * }
 * 
 * // Now safe to make authenticated API calls
 * ```
 */
export function useAuthReady() {
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    let mounted = true;
    let sessionChecked = false;
    let authStateReceived = false;

    const checkIfReady = () => {
      // Mark ready only after BOTH session check AND auth state listener fires
      if (sessionChecked && authStateReceived && mounted) {
        setIsAuthReady(true);
      }
    };

    // Wait for session restoration to complete
    const initAuth = async () => {
      try {
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        
        if (!mounted) return;
        
        setSession(currentSession);
        sessionChecked = true;
        checkIfReady();
      } catch (error) {
        console.error('Failed to restore session:', error);
        if (mounted) {
          sessionChecked = true;
          checkIfReady();
        }
      }
    };

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, newSession) => {
      if (!mounted) return;
      
      setSession(newSession);
      authStateReceived = true;
      checkIfReady();
    });

    initAuth();

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  return {
    isAuthReady,
    session,
    isAuthenticated: !!session,
  };
}
