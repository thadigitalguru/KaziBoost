const paymentKPIs = [
  { label: 'Pending checkouts', value: '14', note: 'Awaiting confirmation' },
  { label: 'Reconciled today', value: '23', note: 'Synced with CRM records' },
  { label: 'Refunds queued', value: '3', note: 'Review before approval' },
  { label: 'Provider health', value: 'Healthy', note: 'STK push latency within target' },
];

const checkoutSteps = [
  'Collect phone number, amount, and order reference',
  'Initiate M-Pesa STK push with KES validation',
  'Record callback outcome and provider transaction id',
  'Match payment to contact, refund, or order record',
];

const reconciliationFilters = ['Status', 'Provider transaction id', 'Contact', 'Date range', 'Failure reason'];

const ledger = [
  {
    reference: 'BOOKING-001',
    phone: '+254 700 123 456',
    amount: 'KES 1,500',
    status: 'Success',
    providerTxId: 'TX-91A2',
  },
  {
    reference: 'ORDER-042',
    phone: '+254 711 222 333',
    amount: 'KES 6,200',
    status: 'Pending',
    providerTxId: '—',
  },
  {
    reference: 'INVOICE-118',
    phone: '+254 723 444 555',
    amount: 'KES 2,750',
    status: 'Failed',
    providerTxId: 'TX-55B7',
  },
];

const providerRegistry = [
  { name: 'M-Pesa', channel: 'STK push', status: 'Primary', note: 'Kenya checkout and callbacks' },
  { name: 'Card gateway', channel: 'API checkout', status: 'Ready', note: 'Fallback for card payments' },
  { name: 'Bank transfer', channel: 'Manual reconcile', status: 'Available', note: 'For high-value settlements' },
];

const refundFlow = [
  'Open the payment record from reconciliation',
  'Confirm the amount, reason, and approval trail',
  'Issue the refund and update the payment state',
  'Notify the customer and link the event to the timeline',
];

export default function PaymentsWorkspacePage() {
  return (
    <main className="page-shell">
      <section className="hero compact">
        <p className="eyebrow">Payments</p>
        <h1>Reconciliation and checkout UI</h1>
        <p className="lede">
          Capture local checkout flows, track callback outcomes, and reconcile payments
          against contacts and orders from the same workspace.
        </p>
        <div className="cta-row">
          <a className="button primary" href="/dashboard/analytics">
            Review revenue trends
          </a>
          <a className="button secondary" href="/dashboard">
            Back to dashboard
          </a>
        </div>
      </section>

      <section className="metric-grid">
        {paymentKPIs.map((item) => (
          <article key={item.label} className="metric-card">
            <p>{item.label}</p>
            <strong>{item.value}</strong>
            <span>{item.note}</span>
          </article>
        ))}
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Checkout</h2>
          <p>Initiate a payment with the same controls used by the backend API.</p>
          <label className="field">
            <span>Phone number</span>
            <input type="tel" defaultValue="+254700123456" aria-label="Checkout phone number" />
          </label>
          <label className="field">
            <span>Amount</span>
            <input type="number" defaultValue={1500} aria-label="Checkout amount" />
          </label>
          <label className="field">
            <span>Reference</span>
            <input type="text" defaultValue="BOOKING-001" aria-label="Checkout reference" />
          </label>
          <label className="field">
            <span>Currency</span>
            <select defaultValue="KES" aria-label="Checkout currency">
              <option value="KES">KES</option>
              <option value="USD">USD</option>
            </select>
          </label>
          <div className="cta-row">
            <button className="button primary" type="button">
              Send STK push
            </button>
            <button className="button secondary" type="button">
              Save draft
            </button>
          </div>
        </article>

        <article className="panel">
          <h2>Reconciliation filters</h2>
          <p>Narrow down the ledger by callback status or provider transaction id.</p>
          <ul className="pill-list">
            {reconciliationFilters.map((filter) => (
              <li key={filter}>{filter}</li>
            ))}
          </ul>
          <div className="stack">
            {providerRegistry.map((provider) => (
              <article key={provider.name} className="schedule-item">
                <div className="schedule-head">
                  <strong>{provider.name}</strong>
                  <span>{provider.status}</span>
                </div>
                <p>{provider.channel}</p>
                <p>{provider.note}</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="grid two-up">
        <article className="panel">
          <h2>Transaction ledger</h2>
          <div className="stack">
            {ledger.map((payment) => (
              <article key={payment.reference} className="inbox-item">
                <div className="inbox-row">
                  <div>
                    <strong>{payment.reference}</strong>
                    <p>{payment.phone}</p>
                  </div>
                  <span>{payment.status}</span>
                </div>
                <p>Amount: {payment.amount}</p>
                <p>Provider tx id: {payment.providerTxId}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Refund workflow</h2>
          <p>Review the approval path before issuing a refund.</p>
          <ol>
            {refundFlow.map((step, index) => (
              <li key={step}>
                <span>{index + 1}.</span> {step}
              </li>
            ))}
          </ol>
          <div className="cta-row">
            <button className="button primary" type="button">
              Create refund
            </button>
            <button className="button secondary" type="button">
              Open summary
            </button>
          </div>
        </article>
      </section>

      <section className="panel">
        <h2>Checkout flow</h2>
        <ol>
          {checkoutSteps.map((step, index) => (
            <li key={step}>
              <span>{index + 1}.</span> {step}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
