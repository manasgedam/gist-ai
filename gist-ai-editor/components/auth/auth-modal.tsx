'use client'

import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { supabase } from '@/lib/supabase'

export function AuthModal() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="w-full max-w-md p-8 bg-card rounded-lg border border-border shadow-lg">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold mb-2">Gist AI</h1>
          <p className="text-sm text-muted-foreground">
            Sign in to start creating viral content
          </p>
        </div>
        <Auth
          supabaseClient={supabase}
          appearance={{ 
            theme: ThemeSupa,
            variables: {
              default: {
                colors: {
                  brand: 'hsl(var(--primary))',
                  brandAccent: 'hsl(var(--primary))',
                }
              }
            }
          }}
          providers={['google', 'github']}
          redirectTo={typeof window !== 'undefined' ? `${window.location.origin}/` : undefined}
          onlyThirdPartyProviders
        />
      </div>
    </div>
  )
}
