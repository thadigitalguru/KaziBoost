const kpis = [
  { label: 'Active workspaces', value: '6', change: '+2 this week' },
  { label: 'Briefs scheduled', value: '14', change: '4 due today' },
  { label: 'Generated drafts', value: '23', change: '83% approved' },
  { label: 'Top language', value: 'Swahili', change: 'Higher CTR than English' },
];

const workspaces = [
  {
    name: 'Local services',
    keyword: 'salon near me',
    language: 'English / Swahili',
    status: 'Ready for review',
    note: 'Includes homepage, FAQ, and a bilingual service page.',
  },
  {
    name: 'Retail growth',
    keyword: 'hardware store Nairobi',
    language: 'English',
    status: 'Scheduled',
    note: 'Pairs a category page with product-led blog support.',
  },
  {
    name: 'Content refresh',
    keyword: 'booking reminder WhatsApp',
    language: 'Sheng / Swahili',
    status: 'Needs approval',
    note: 'Drafts a WhatsApp follow-up guide and a CTA landing page.',
  },
];

const contentBriefs = [
  {
    title: 'Homepage hero rewrite',
    keyword: 'salon near me',
    format: 'Landing page',
    tone: 'Helpful',
    length: 'Short',
  },
  {
    title: 'Localized FAQ',
    keyword: 'do you deliver on weekends',
    format: 'FAQ',
    tone: 'Conversational',
    length: 'Medium',
  },
  {
    title: 'Topic cluster article',
    keyword: 'how to get more bookings',
    format: 'Blog post',
    tone: 'Expert',
    length: 'Long',
  },
];

const topicMap = [
  'Main topic: local SEO for SMEs',
  'Cluster: service pages, FAQ schema, and reviews',
  'Cluster: WhatsApp conversion and follow-up content',
  'Cluster: bilingual landing pages for multilingual audiences',
];

const calendarItems = [
  {
    title: 'Swahili service page refresh',
    due: 'Today · 15:00',
    status: 'In review',
    owner: 'Amina',
  },
  {
    title: 'WhatsApp booking guide',
    due: 'Tomorrow · 10:30',
    status: 'Draft ready',
    owner: 'Grace',
  },
  {
    title: 'SEO topic map update',
    due: 'Fri · 09:00',
    status: 'Scheduled',
    owner: 'SEO lead',
  },
  {
    title: 'Blog post for hardware sales',
    due: 'Mon · 13:00',
    status: 'Needs approval',
    owner: 'Content team',
  },
];

const filters = ['Workspace', 'Language', 'Status', 'Due date', 'Owner'];
const workflowSteps = [
  'Choose a keyword workspace and confirm the target language',
  'Generate the brief, meta copy, and internal linking suggestions',
  'Review the draft for safety, tone, and local relevance',
  'Schedule publication, then track performance in analytics',
];

export default function SeoWorkspacePage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">SEO</p>
        <h1>Calendar and content workflow</h1>
        <p className="lede">
          Plan keyword workspaces, generate localized briefs, and keep the publishing
          calendar aligned with the site builder, analytics, and training content.
        </p>
        <div className="cta-row">
          <a className="button primary" href="/dashboard/sites/new">
            Start a new site brief
          </a>
          <a className="button secondary" href="/dashboard">
            Back to dashboard
          </a>
        </div>
      </section>

      <section className="metric-grid">
        {kpis.map((metric) => (
          <article key={metric.label} className="metric-card">
            <p>{metric.label}</p>
            <strong>{metric.value}</strong>
            <span>{metric.change}</span>
          </article>
        ))}
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Keyword workspaces</h2>
          <p>Track the active briefs that feed content generation and scheduling.</p>
          <ul className="pill-list">
            {filters.map((filter) => (
              <li key={filter}>{filter}</li>
            ))}
          </ul>
          <div className="stack">
            {workspaces.map((workspace) => (
              <article key={workspace.name} className="schedule-item">
                <div className="schedule-head">
                  <strong>{workspace.name}</strong>
                  <span>{workspace.status}</span>
                </div>
                <p>{workspace.keyword}</p>
                <p>{workspace.language}</p>
                <p>{workspace.note}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Content generation</h2>
          <p>Seed a draft with the same structure used by the backend SEO assistant.</p>
          <label className="field">
            <span>Seed keyword</span>
            <input type="text" defaultValue="salon near me" aria-label="Seed keyword" />
          </label>
          <label className="field">
            <span>Content type</span>
            <select defaultValue="blog" aria-label="Content type">
              <option value="blog">Blog post</option>
              <option value="faq">FAQ</option>
              <option value="landing">Landing page</option>
            </select>
          </label>
          <label className="field">
            <span>Language</span>
            <select defaultValue="sw" aria-label="Content language">
              <option value="en">English</option>
              <option value="sw">Swahili</option>
              <option value="sh">Sheng</option>
            </select>
          </label>
          <div className="cta-row">
            <button className="button primary" type="button">
              Generate brief
            </button>
            <button className="button secondary" type="button">
              Save to workspace
            </button>
          </div>

          <div className="stack">
            {contentBriefs.map((brief) => (
              <article key={brief.title} className="inbox-item">
                <div className="inbox-row">
                  <div>
                    <strong>{brief.title}</strong>
                    <p>{brief.keyword}</p>
                  </div>
                  <span>{brief.format}</span>
                </div>
                <div className="chip-row">
                  <span className="chip">{brief.tone}</span>
                  <span className="chip">{brief.length}</span>
                </div>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Publishing calendar</h2>
          <p>Review due items and keep content moving without losing approvals.</p>
          <div className="stack">
            {calendarItems.map((item) => (
              <article key={item.title} className="status-item">
                <div className="inbox-row">
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.due}</p>
                  </div>
                  <span>{item.status}</span>
                </div>
                <p>Owner: {item.owner}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Topic map and workflow</h2>
          <p>Connect briefs to topic clusters so every article supports the next one.</p>
          <ul className="checklist">
            {topicMap.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <h3>Workflow steps</h3>
          <ol>
            {workflowSteps.map((step, index) => (
              <li key={step}>
                <span>{index + 1}.</span> {step}
              </li>
            ))}
          </ol>
        </article>
      </section>
    </main>
  );
}
