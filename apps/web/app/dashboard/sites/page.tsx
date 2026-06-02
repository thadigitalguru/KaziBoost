const sites = [
  {
    name: 'Amina Salon',
    status: 'Draft',
    template: 'Beauty and wellness',
    language: 'English / Swahili',
    nextStep: 'Open publish flow',
  },
  {
    name: 'Kamau Hardware',
    status: 'Published',
    template: 'Retail storefront',
    language: 'English',
    nextStep: 'Connect custom domain',
  },
  {
    name: 'Otieno Tutoring',
    status: 'Reviewing SEO',
    template: 'Professional services',
    language: 'English / Sheng',
    nextStep: 'Add bilingual variant',
  },
];

const steps = [
  'Choose a template matched to the business type',
  'Set the site name, primary language, and brand tone',
  'Add first pages and confirm SEO artifacts',
  'Preview mobile rendering and language switcher',
  'Publish, attach a domain, and share the live URL',
];

export default function SitesWorkspacePage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">Sites</p>
        <h1>Website publish flow</h1>
        <p className="lede">
          Guide an SME from template selection to live publishing with SEO artifacts,
          language variants, preview checks, and domain setup.
        </p>
        <div className="cta-row">
          <a className="button primary" href="/dashboard/sites/new">
            Start new site
          </a>
          <a className="button secondary" href="/dashboard">
            Back to dashboard
          </a>
        </div>
      </section>

      <section className="grid">
        {sites.map((site) => (
          <article key={site.name} className="card">
            <p className="eyebrow">{site.status}</p>
            <h2>{site.name}</h2>
            <p>Template: {site.template}</p>
            <p>Languages: {site.language}</p>
            <p>Next step: {site.nextStep}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>Publish flow checklist</h2>
        <ol>
          {steps.map((step, index) => (
            <li key={step}>
              <span>{index + 1}.</span> {step}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
