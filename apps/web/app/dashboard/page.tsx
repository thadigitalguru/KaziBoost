import { redirect } from 'next/navigation';

import { fetchReadiness, type Readiness } from '../../lib/api';
import LogoutButton from './logout-button';
import { getCurrentAuthSession } from '../../lib/auth-session';

const modules = [
  { name: 'Sites', status: 'website publish flow UI in progress', href: '/dashboard/sites' },
  { name: 'CRM', status: 'lead inbox and contact timeline in progress', href: '/dashboard/crm' },
  { name: 'WhatsApp', status: 'conversation workspace in progress', href: '/dashboard/whatsapp' },
  { name: 'Payments', status: 'reconciliation and checkout UI in progress', href: '/dashboard/payments' },
  { name: 'Analytics', status: 'reporting overview and scheduling in progress', href: '/dashboard/analytics' },
  { name: 'SEO', status: 'calendar and content workflow UI in progress', href: '/dashboard/seo' },
  { name: 'Training', status: 'knowledge base shell in progress', href: '/dashboard/training' },
];

async function getReadiness(): Promise<Readiness | null> {
  try {
    return await fetchReadiness();
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const [readiness, session] = await Promise.all([getReadiness(), getCurrentAuthSession()]);

  if (!session) {
    redirect('/login');
  }

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="inbox-row hero-header">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h1>Operational overview</h1>
          </div>
          <LogoutButton />
        </div>
        <p className="lede">
          Welcome back, {session.user.owner_name}. This shell is ready for the first end-to-end customer journey:
          site publish, lead capture, WhatsApp follow-up, and analytics visibility.
        </p>
      </section>

      <section className="panel" aria-live="polite">
        <div className="inbox-row">
          <div>
            <h2>API readiness</h2>
            <p>{readiness ? 'Live service status from the configured API.' : 'API status is unavailable. Configure the API URL or check the service.'}</p>
          </div>
          <span className={readiness?.status === 'ready' ? 'status-ok' : 'status-warning'}>
            {readiness?.status ?? 'Unavailable'}
          </span>
        </div>
        {readiness ? (
          <ul className="checklist">
            {Object.entries(readiness.checks).map(([name, status]) => (
              <li key={name}><strong>{name}</strong>: {status}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="grid">
        {modules.map((item) => (
          <article key={item.name} className="card">
            <h2>{item.name}</h2>
            <p>{item.status}</p>
            <a className="button secondary" href={item.href}>Open</a>
          </article>
        ))}
      </section>
    </main>
  );
}
