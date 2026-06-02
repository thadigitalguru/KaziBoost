const templates = [
  'Beauty and wellness',
  'Retail storefront',
  'Professional services',
  'Food and hospitality',
];

const seoChecklist = [
  'Meta title and description are auto-generated',
  'sitemap.xml and robots.txt are available after publish',
  'LocalBusiness schema includes business name, phone, and location',
  'hreflang links are shown when multiple language variants exist',
  'Mobile preview matches the default viewport',
];

const publishSteps = [
  'Name your site and select a template',
  'Pick the primary language and add a secondary language if needed',
  'Create the homepage and first support page',
  'Verify SEO artifacts and preview on mobile',
  'Publish and optionally connect a custom domain',
];

export default function NewSitePage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">New site</p>
        <h1>Create and publish a website</h1>
        <p className="lede">
          This flow is designed for a guided first launch: template selection, content setup,
          language choices, SEO validation, and publish.
        </p>
      </section>

      <section className="grid">
        <article className="card">
          <h2>1. Site details</h2>
          <p>Set the business name, brand tone, and launch goal.</p>
          <label className="field">
            <span>Site name</span>
            <input defaultValue="Amina Salon" />
          </label>
          <label className="field">
            <span>Primary language</span>
            <select defaultValue="English">
              <option>English</option>
              <option>Swahili</option>
              <option>Sheng</option>
            </select>
          </label>
        </article>

        <article className="card">
          <h2>2. Template selection</h2>
          <p>Choose a template matched to the business type and conversion goal.</p>
          <ul className="pill-list">
            {templates.map((template) => (
              <li key={template}>{template}</li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2>3. Publish readiness</h2>
          <p>Confirm that the page is ready for first-time visitors and search engines.</p>
          <ul className="checklist">
            {seoChecklist.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="panel">
        <h2>Guided publish steps</h2>
        <ol>
          {publishSteps.map((step, index) => (
            <li key={step}>
              <span>{index + 1}.</span> {step}
            </li>
          ))}
        </ol>
        <div className="cta-row">
          <button className="button primary" type="button">
            Publish site
          </button>
          <button className="button secondary" type="button">
            Save draft
          </button>
        </div>
      </section>
    </main>
  );
}
