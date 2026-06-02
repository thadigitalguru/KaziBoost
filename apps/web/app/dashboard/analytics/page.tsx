const kpis = [
  { label: 'Qualified leads', value: '128', change: '+18%' },
  { label: 'Website conversions', value: '9.4%', change: '+1.2%' },
  { label: 'WhatsApp replies', value: '76%', change: '+7%' },
  { label: 'Revenue proxy', value: 'KES 482k', change: '+11%' },
];

const trendSeries = [
  { label: 'Mon', value: 38 },
  { label: 'Tue', value: 52 },
  { label: 'Wed', value: 46 },
  { label: 'Thu', value: 61 },
  { label: 'Fri', value: 72 },
  { label: 'Sat', value: 67 },
  { label: 'Sun', value: 41 },
];

const connectors = [
  { name: 'GA4', status: 'Connected', note: 'Last sync 12 min ago' },
  { name: 'Search Console', status: 'Connected', note: 'Queries updated this morning' },
  { name: 'CRM source tracking', status: 'Healthy', note: 'Attribution flowing normally' },
];

const reportSchedules = [
  { name: 'Weekly owner summary', cadence: 'Every Monday 08:00', audience: 'Owner' },
  { name: 'Sales follow-up digest', cadence: 'Tue / Thu 17:30', audience: 'Manager' },
  { name: 'Monthly ROI report', cadence: '1st of month 09:00', audience: 'Stakeholders' },
];

const nextActions = [
  'Review site traffic and conversion trends',
  'Check report delivery status and recipients',
  'Adjust the schedule cadence for active campaigns',
  'Open connectors to confirm data freshness',
  'Export CSV or PDF when presenting performance',
];

export default function AnalyticsWorkspacePage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">Analytics</p>
        <h1>Reporting overview and schedule controls</h1>
        <p className="lede">
          Track lead growth, website activity, and follow-up performance with a dashboard
          that pairs insight cards with schedule management for recurring summaries.
        </p>
        <div className="cta-row">
          <a className="button primary" href="/dashboard/crm">
            Review lead sources
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
          <h2>Weekly trend snapshot</h2>
          <p>Lead activity across the most recent seven days.</p>
          <div className="bar-chart" aria-label="Lead trend chart">
            {trendSeries.map((point) => (
              <div key={point.label} className="bar-column">
                <div className="bar-track">
                  <div className="bar-fill" style={{ height: `${point.value}%` }} />
                </div>
                <span>{point.label}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Connector status</h2>
          <div className="stack">
            {connectors.map((connector) => (
              <article key={connector.name} className="status-item">
                <div className="inbox-row">
                  <div>
                    <strong>{connector.name}</strong>
                    <p>{connector.note}</p>
                  </div>
                  <span>{connector.status}</span>
                </div>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Scheduled reports</h2>
          <div className="stack">
            {reportSchedules.map((schedule) => (
              <article key={schedule.name} className="schedule-item">
                <div className="schedule-head">
                  <strong>{schedule.name}</strong>
                  <span>{schedule.audience}</span>
                </div>
                <p>{schedule.cadence}</p>
              </article>
            ))}
          </div>
          <div className="cta-row">
            <button className="button primary" type="button">
              Add schedule
            </button>
            <button className="button secondary" type="button">
              Export PDF
            </button>
          </div>
        </article>

        <article className="panel">
          <h2>Next actions</h2>
          <ol>
            {nextActions.map((action, index) => (
              <li key={action}>
                <span>{index + 1}.</span> {action}
              </li>
            ))}
          </ol>
        </article>
      </section>
    </main>
  );
}
