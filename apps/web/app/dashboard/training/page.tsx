const knowledgeBaseStats = [
  { label: 'Published articles', value: '42', note: '8 featured for onboarding' },
  { label: 'Top search topics', value: '12', note: 'Most searched this week' },
  { label: 'Avg. time to answer', value: '2m 14s', note: 'From search to article open' },
  { label: 'Completion rate', value: '81%', note: 'Onboarding checklist progress' },
];

const categories = ['Onboarding', 'SEO', 'CRM', 'WhatsApp', 'Payments', 'Analytics'];

const featuredArticles = [
  {
    title: 'Getting started with KaziBoost',
    summary: 'A guided overview of the first setup steps for owners and operators.',
    tag: 'Onboarding',
  },
  {
    title: 'Publishing your first site',
    summary: 'Recommended launch flow, page structure, and SEO checks before going live.',
    tag: 'Website',
  },
  {
    title: 'Using the CRM inbox effectively',
    summary: 'How to triage new leads, add notes, and assign contacts for follow-up.',
    tag: 'CRM',
  },
];

const onboardingSteps = [
  'Create the tenant and confirm owner access',
  'Publish a site and capture the first lead',
  'Reply in WhatsApp and schedule a reminder',
  'Reconcile a payment and review the customer record',
];

const topContent = [
  { title: 'How to update a training article', views: '1.2k views', status: 'Frequently opened' },
  { title: 'FAQ template for new customers', views: '948 views', status: 'Used in onboarding' },
  { title: 'Payment troubleshooting guide', views: '812 views', status: 'Common support path' },
];

const shellActions = [
  'Search the knowledge base by keyword or category',
  'Open featured content from the onboarding panel',
  'Review top articles and assign owners',
  'Duplicate a guide to create a localized variant',
];

export default function TrainingKnowledgeBasePage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">Training</p>
        <h1>Knowledge base and onboarding content shell</h1>
        <p className="lede">
          Centralize how-to content, onboarding paths, and support references so the team
          can find answers quickly and turn product knowledge into a repeatable workflow.
        </p>
        <div className="cta-row">
          <a className="button primary" href="/dashboard">
            Back to dashboard
          </a>
          <button className="button secondary" type="button">
            Create article
          </button>
        </div>
      </section>

      <section className="metric-grid">
        {knowledgeBaseStats.map((item) => (
          <article key={item.label} className="metric-card">
            <p>{item.label}</p>
            <strong>{item.value}</strong>
            <span>{item.note}</span>
          </article>
        ))}
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Search and category filters</h2>
          <p>Use filters to narrow content by topic, intent, and article type.</p>
          <label className="field">
            <span>Search</span>
            <input type="search" defaultValue="localized onboarding" aria-label="Search training articles" />
          </label>
          <label className="field">
            <span>Category</span>
            <select defaultValue="Onboarding" aria-label="Filter training articles by category">
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
          <ul className="pill-list">
            {categories.map((category) => (
              <li key={category}>{category}</li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <h2>Onboarding path</h2>
          <p>A linear path for new team members and customers to follow.</p>
          <ol>
            {onboardingSteps.map((step, index) => (
              <li key={step}>
                <span>{index + 1}.</span> {step}
              </li>
            ))}
          </ol>
          <div className="cta-row">
            <button className="button primary" type="button">
              Share guide
            </button>
            <button className="button secondary" type="button">
              Duplicate path
            </button>
          </div>
        </article>
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Featured articles</h2>
          <div className="stack">
            {featuredArticles.map((article) => (
              <article key={article.title} className="inbox-item">
                <div className="inbox-row">
                  <div>
                    <strong>{article.title}</strong>
                    <p>{article.summary}</p>
                  </div>
                  <span>{article.tag}</span>
                </div>
                <div className="chip-row">
                  <span className="chip">Featured</span>
                  <span className="chip">Editable</span>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Top content</h2>
          <div className="stack">
            {topContent.map((item) => (
              <article key={item.title} className="schedule-item">
                <div className="schedule-head">
                  <strong>{item.title}</strong>
                  <span>{item.views}</span>
                </div>
                <p>{item.status}</p>
              </article>
            ))}
          </div>
          <div className="cta-row">
            <button className="button primary" type="button">
              Review analytics
            </button>
            <button className="button secondary" type="button">
              Open drafts
            </button>
          </div>
        </article>
      </section>

      <section className="panel">
        <h2>Shell actions</h2>
        <ol>
          {shellActions.map((action, index) => (
            <li key={action}>
              <span>{index + 1}.</span> {action}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
