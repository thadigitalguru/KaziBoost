const modules = [
  { name: 'Sites', status: 'website publish flow UI in progress', href: '/dashboard/sites' },
  { name: 'CRM', status: 'lead inbox and contact timeline in progress', href: '/dashboard/crm' },
  { name: 'WhatsApp', status: 'conversation workspace in progress', href: '/dashboard/whatsapp' },
  { name: 'Payments', status: 'reconciliation and checkout UI in progress', href: '/dashboard/payments' },
  { name: 'Analytics', status: 'reporting overview and scheduling in progress', href: '/dashboard/analytics' },
  { name: 'SEO', status: 'calendar and content workflow UI in progress', href: '/dashboard/seo' },
  { name: 'Training', status: 'knowledge base shell in progress', href: '/dashboard/training' },
];

export default function DashboardPage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">Dashboard</p>
        <h1>Operational overview</h1>
        <p className="lede">
          This shell is ready for the first end-to-end customer journey: site publish,
          lead capture, WhatsApp follow-up, and analytics visibility.
        </p>
      </section>

      <section className="grid">
        {modules.map((item) => (
          <article key={item.name} className="card">
            <h2>{item.name}</h2>
            <p>{item.status}</p>
            {item.href ? (
              <a className="button secondary" href={item.href}>
                Open
              </a>
            ) : null}
          </article>
        ))}
      </section>
    </main>
  );
}
