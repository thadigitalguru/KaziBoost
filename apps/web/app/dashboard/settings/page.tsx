import { redirect } from 'next/navigation';

import LogoutButton from '../logout-button';
import SettingsForm from './settings-form';
import { getCurrentAuthSession } from '../../../lib/auth-session';

export default async function SettingsPage() {
  const session = await getCurrentAuthSession();

  if (!session) {
    redirect('/login?returnTo=/dashboard/settings');
  }

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="inbox-row hero-header">
          <div>
            <p className="eyebrow">Settings</p>
            <h1>Operational settings and tenant controls</h1>
          </div>
          <LogoutButton />
        </div>
        <p className="lede">
          Keep tenant identity and owner details accurate so onboarding, support, and customer-facing pages stay aligned.
        </p>
      </section>

      <section className="grid two-up">
        <article className="card">
          <h2>Current access</h2>
          <p><strong>Tenant:</strong> {session.tenant.name}</p>
          <p><strong>Owner:</strong> {session.user.owner_name}</p>
          <p><strong>Email:</strong> {session.user.email}</p>
          <p><strong>Role:</strong> {session.user.role}</p>
        </article>
        <SettingsForm businessName={session.tenant.name} ownerName={session.user.owner_name} />
      </section>
    </main>
  );
}
