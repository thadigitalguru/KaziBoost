'use client';

export default function DashboardError({ reset }: { reset: () => void }) {
  return (
    <main className="page-shell">
      <section className="hero compact" role="alert">
        <p className="eyebrow">Dashboard</p>
        <h1>We couldn’t load this workspace.</h1>
        <p className="lede">The dashboard is temporarily unavailable. Try again or return to the home page.</p>
        <div className="cta-row">
          <button className="button primary" type="button" onClick={reset}>Try again</button>
          <a className="button secondary" href="/">Return home</a>
        </div>
      </section>
    </main>
  );
}
