'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { ApiClientError, logout } from '../../lib/api-client';

export default function LogoutButton() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogout() {
    setSubmitting(true);
    setError(null);
    try {
      await logout();
      router.replace('/login');
      router.refresh();
    } catch (reason) {
      setError(reason instanceof ApiClientError ? reason.message : 'Unable to sign out right now.');
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-actions">
      <button className="button secondary" type="button" onClick={handleLogout} disabled={submitting}>
        {submitting ? 'Signing out…' : 'Sign out'}
      </button>
      {error ? <p className="form-error auth-error" role="alert">{error}</p> : null}
    </div>
  );
}
