const threads = [
  {
    contact: 'Amina Otieno',
    preview: 'Can I get a booking reminder for Saturday morning?',
    status: 'Open',
    assignee: 'Grace',
    channel: 'WhatsApp',
  },
  {
    contact: 'Brian Kamau',
    preview: 'The item is out of stock — when will it be back?',
    status: 'Waiting on reply',
    assignee: 'Team queue',
    channel: 'WhatsApp',
  },
  {
    contact: 'Diana Wanjiku',
    preview: 'Thanks, I will confirm payment after lunch.',
    status: 'Handoff complete',
    assignee: 'Sales',
    channel: 'WhatsApp',
  },
];

const workspaceTools = [
  'FAQ bot reply suggestions',
  'Human handoff assignment',
  'Reminder scheduling',
  'Conversation search by phone',
  'Overdue queue visibility',
];

const activeConversation = [
  { speaker: 'Customer', text: 'Hi, do you have weekend slots?' },
  { speaker: 'Bot', text: 'Yes — we have Saturday morning and afternoon availability.' },
  { speaker: 'Customer', text: 'Great, please reserve 10:00 AM.' },
  { speaker: 'Agent', text: 'Confirmed. We will send a reminder on Friday evening.' },
];

export default function WhatsAppWorkspacePage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">WhatsApp</p>
        <h1>Conversation workspace</h1>
        <p className="lede">
          Manage threads, approve bot replies, and hand off to humans when a conversation
          needs a personal touch or a payment confirmation.
        </p>
        <div className="cta-row">
          <a className="button primary" href="/dashboard/crm">
            Sync with CRM
          </a>
          <a className="button secondary" href="/dashboard">
            Back to dashboard
          </a>
        </div>
      </section>

      <section className="grid">
        <article className="card">
          <h2>Workspace tools</h2>
          <ul className="pill-list">
            {workspaceTools.map((tool) => (
              <li key={tool}>{tool}</li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2>Thread health</h2>
          <p>Open threads today: 14</p>
          <p>Awaiting human handoff: 5</p>
          <p>Reminder queue due today: 3</p>
        </article>
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Inbox</h2>
          <div className="stack">
            {threads.map((thread) => (
              <article key={thread.contact} className="inbox-item">
                <div className="inbox-row">
                  <div>
                    <strong>{thread.contact}</strong>
                    <p>{thread.channel} · {thread.status}</p>
                  </div>
                  <span>{thread.assignee}</span>
                </div>
                <p>{thread.preview}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Active conversation</h2>
          <p className="eyebrow">Amina Otieno</p>
          <div className="conversation">
            {activeConversation.map((message) => (
              <div key={message.text} className={`message ${message.speaker.toLowerCase()}`}>
                <strong>{message.speaker}</strong>
                <p>{message.text}</p>
              </div>
            ))}
          </div>
          <div className="cta-row">
            <button className="button primary" type="button">Send reply</button>
            <button className="button secondary" type="button">Hand off to agent</button>
          </div>
        </article>
      </section>
    </main>
  );
}
