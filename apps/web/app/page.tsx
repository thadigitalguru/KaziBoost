const highlights = [
  {
    title: 'Publish faster',
    description: 'Launch mobile-first pages with SEO scaffolding and language variants.',
  },
  {
    title: 'Capture leads',
    description: 'Turn visits into contacts with forms, timelines, tags, and source attribution.',
  },
  {
    title: 'Close on WhatsApp and M-Pesa',
    description: 'Connect conversations, handoff, reminders, and payment reconciliation.',
  },
  {
    title: 'See ROI clearly',
    description: 'Track traffic, conversions, scheduling, and performance across each tenant.',
  },
];

const nextBuilds = [
  'SEO calendar and content workflow UI',
  'Operational settings and tenant controls',
  'More product polish on the core onboarding journey',
  'Field feedback and usability refinements',
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">KaziBoost</p>
        <h1>Growth software for Kenyan SMEs.</h1>
        <p className="lede">
          Build a local presence, capture first-party leads, automate WhatsApp follow-up,
          and connect M-Pesa payments to real business outcomes.
        </p>

        <div className="cta-row">
          <a className="button primary" href="/dashboard">
            Open dashboard
          </a>
          <a className="button secondary" href="http://localhost:8000/health" target="_blank" rel="noreferrer">
            Check API health
          </a>
        </div>
      </section>

      <section className="grid">
        {highlights.map((item) => (
          <article key={item.title} className="card">
            <h2>{item.title}</h2>
            <p>{item.description}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>Suggested next builds</h2>
        <ol>
          {nextBuilds.map((item, index) => (
            <li key={item}>
              <span>{index + 1}.</span> {item}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
