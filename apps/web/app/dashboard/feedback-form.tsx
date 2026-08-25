'use client';

import { FormEvent, useState } from 'react';

import { ApiClientError, submitFeedback } from '../../lib/api-client';

export default function FeedbackForm() {
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setStatus(null);
    try {
      const response = await submitFeedback({ page: '/dashboard', message });
      setStatus(`Thanks — feedback ${response.feedback_id} received.`);
      setMessage('');
    } catch (reason) {
      setStatus(reason instanceof ApiClientError ? reason.message : 'Unable to send feedback right now.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="panel feedback-form" onSubmit={handleSubmit}>
      <h2>Share feedback</h2>
      <p>Tell us what feels confusing or what should be faster in the onboarding journey.</p>
      <label className="field">
        <span>Message</span>
        <textarea rows={4} value={message} onChange={(event) => setMessage(event.target.value)} placeholder="What should we improve next?" required />
      </label>
      {status ? <p className="settings-note" role="status">{status}</p> : null}
      <button className="button primary" type="submit" disabled={submitting || message.trim().length === 0}>
        {submitting ? 'Sending…' : 'Send feedback'}
      </button>
    </form>
  );
}
