import LoginForm from './login-form';

export default function LoginPage({
  searchParams,
}: {
  searchParams?: { returnTo?: string | string[] };
}) {
  const candidate = searchParams?.returnTo;
  const returnTo = typeof candidate === 'string' && candidate.startsWith('/') ? candidate : '/dashboard';

  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">KaziBoost account</p>
        <h1>Sign in to your workspace.</h1>
        <p className="lede">Your access token is protected by a server-managed HttpOnly cookie.</p>
      </section>
      <LoginForm returnTo={returnTo} />
    </main>
  );
}
