'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

import { ApiClientError, login } from '../../lib/api-client';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.push('/dashboard');
      router.refresh();
    } catch (reason) {
      setError(reason instanceof ApiClientError ? reason.message : 'Unable to sign in. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">KaziBoost account</p>
        <h1>Sign in to your workspace.</h1>
        <p className="lede">Your access token is protected by a server-managed HttpOnly cookie.</p>
      </section>
      <form className="panel auth-form" onSubmit={submit}>
        <label className="field">
          <span>Email</span>
          <input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label className="field">
          <span>Password</span>
          <input type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {error ? <p className="form-error" role="alert">{error}</p> : null}
        <button className="button primary" type="submit" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </main>
  );
}
