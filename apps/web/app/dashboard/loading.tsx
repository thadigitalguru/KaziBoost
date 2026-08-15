export default function Loading() {
  return (
    <main className="page-shell" aria-busy="true">
      <section className="hero compact">
        <p className="eyebrow">Dashboard</p>
        <h1>Loading operational overview…</h1>
        <p className="lede">Checking the configured API and preparing your workspaces.</p>
      </section>
    </main>
  );
}
