const leads = [
  {
    name: 'Amina Otieno',
    source: 'Web form',
    status: 'New lead',
    tags: ['booking', 'salon'],
    lastNote: 'Asked for weekend appointment slots and pricing.',
    value: 'High intent',
  },
  {
    name: 'Brian Kamau',
    source: 'WhatsApp',
    status: 'In follow-up',
    tags: ['hardware', 'quote'],
    lastNote: 'Waiting on updated quotation and delivery timing.',
    value: 'Medium intent',
  },
  {
    name: 'Diana Wanjiku',
    source: 'Manual import',
    status: 'Nurture',
    tags: ['newsletter', 'b2b'],
    lastNote: 'Added to campaign segment for monthly check-ins.',
    value: 'Warm contact',
  },
];

const contactTimeline = [
  'Lead submitted a form on the published homepage',
  'Auto-tagged by source and page campaign',
  'Assigned to sales owner for same-day follow-up',
  'Reminder scheduled for WhatsApp outreach',
];

const filters = [
  'Source',
  'Tag',
  'Date range',
  'Intent',
  'Consent status',
];

export default function CRMWorkspacePage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">CRM</p>
        <h1>Lead inbox and contact detail</h1>
        <p className="lede">
          Review incoming leads, inspect the timeline, and prepare fast follow-up from the
          same workspace that powers forms, campaigns, and WhatsApp handoff.
        </p>
        <div className="cta-row">
          <a className="button primary" href="/dashboard/sites/new">
            Capture leads from a site
          </a>
          <a className="button secondary" href="/dashboard">
            Back to dashboard
          </a>
        </div>
      </section>

      <section className="grid">
        <article className="card">
          <h2>Inbox filters</h2>
          <p>Focus on the right contacts with deterministic filters.</p>
          <ul className="pill-list">
            {filters.map((filter) => (
              <li key={filter}>{filter}</li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2>Activity summary</h2>
          <p>New leads appear with source attribution and consent state.</p>
          <p>Total open leads: 18</p>
          <p>Contacts with notes: 11</p>
          <p>Ready for follow-up today: 7</p>
        </article>
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Lead inbox</h2>
          <div className="stack">
            {leads.map((lead) => (
              <article key={lead.name} className="inbox-item">
                <div className="inbox-row">
                  <div>
                    <strong>{lead.name}</strong>
                    <p>{lead.source} · {lead.status}</p>
                  </div>
                  <span>{lead.value}</span>
                </div>
                <p>{lead.lastNote}</p>
                <div className="chip-row">
                  {lead.tags.map((tag) => (
                    <span key={tag} className="chip">{tag}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Contact detail</h2>
          <p className="eyebrow">Amina Otieno</p>
          <p>Phone: +254 712 555 111</p>
          <p>Email: amina@example.com</p>
          <p>Consent: marketing = yes, transactional = yes</p>
          <p>Assigned owner: Grace</p>
          <h3>Timeline</h3>
          <ol>
            {contactTimeline.map((event, index) => (
              <li key={event}>
                <span>{index + 1}.</span> {event}
              </li>
            ))}
          </ol>
          <div className="cta-row">
            <button className="button primary" type="button">Add note</button>
            <button className="button secondary" type="button">Assign owner</button>
          </div>
        </article>
      </section>
    </main>
  );
}
