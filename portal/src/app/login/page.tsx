'use client';

import React, { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

export default function LoginPage() {
  const [email, setEmail] = useState('demo@gini.ai');
  const [password, setPassword] = useState('password');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const res = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (res?.error) {
        setError('Invalid credentials! Try demo@gini.ai / password');
      } else {
        router.push('/');
        router.refresh();
      }
    } catch (err: any) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background-dark flex flex-col items-center justify-center p-4 relative font-sans">
      {/* Decorative vector background accents */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
        <svg className="absolute top-10 left-10 w-24 h-24 text-magenta-pink opacity-40 animate-bounce" style={{ animationDuration: '4s' }} viewBox="0 0 100 100" fill="currentColor">
          <polygon points="50,10 90,90 10,90"></polygon>
        </svg>
        <svg className="absolute bottom-20 right-10 w-16 h-16 text-teal-accent opacity-40" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="8">
          <circle cx="50" cy="50" r="40"></circle>
        </svg>
        <div className="absolute top-1/4 right-1/4 w-12 h-12 bg-spicy-yellow opacity-30 rotate-45"></div>
      </div>

      <div className="w-full max-w-md bg-surface-container neo-border neo-shadow-lg transform -rotate-1 p-8 relative flex flex-col gap-6">
        <div className="flex justify-center items-center gap-2 mb-4">
          <Image src="/gini.png" alt="Gini Logo" width={120} height={40} className="object-contain" priority />
        </div>

        <h2 className="font-space text-2xl font-bold text-center text-spicy-yellow uppercase tracking-wider border-b-4 border-black pb-2">
          Gini Voice Portal
        </h2>

        {error && (
          <div className="bg-magenta-pink text-black p-3 font-semibold neo-border text-center text-sm font-space">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="font-space font-bold uppercase text-xs tracking-wider text-teal-accent">
              Email Address / Login
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-surface-bright text-white px-4 py-3 neo-border text-lg font-space focus:outline-none focus:ring-4 focus:ring-spicy-yellow focus:border-black rounded-none"
              placeholder="Enter email"
              required
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-space font-bold uppercase text-xs tracking-wider text-teal-accent">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="bg-surface-bright text-white px-4 py-3 neo-border text-lg font-space focus:outline-none focus:ring-4 focus:ring-spicy-yellow focus:border-black rounded-none"
              placeholder="Enter password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`mt-4 w-full py-4 neo-border neo-shadow-sm font-space font-bold uppercase tracking-wider text-lg text-black transition-all ${
              loading 
                ? 'bg-gray-500 cursor-not-allowed' 
                : 'bg-spicy-yellow hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-none active:translate-x-1 active:translate-y-1'
            }`}
          >
            {loading ? 'Authenticating...' : 'Enter Session'}
          </button>
        </form>

        <div className="mt-4 border-t-2 border-black pt-4 text-center text-xs text-on-surface-variant font-space uppercase">
          HH Goan Edition © 1994 Gini Corp.
        </div>
      </div>
    </div>
  );
}
