'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

import { ApiClientError, updateSettingsProfile } from '../../../lib/api-client';

export default function SettingsForm({
  businessName,
  ownerName,
}: {
  businessName: string;
  ownerName: string;
}) {
  const router = useRouter();
  const [draftBusinessName, setDraftBusinessName] = useState(businessName);
  const [draftOwnerName, setDraftOwnerName] = useState(ownerName);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await updateSettingsProfile({ business_name: draftBusinessName, owner_name: draftOwnerName });
      setMessage('Settings saved.');
      router.refresh();
    } catch (reason) {
      setMessage(reason instanceof ApiClientError ? reason.message : 'Unable to save settings.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="panel auth-form settings-form" onSubmit={submit}>
      <label className="field">
        <span>Business name</span>
        <input value={draftBusinessName} onChange={(event) => setDraftBusinessName(event.target.value)} />
      </label>
      <label className="field">
        <span>Owner name</span>
        <input value={draftOwnerName} onChange={(event) => setDraftOwnerName(event.target.value)} />
      </label>
      {message ? <p className="form-error settings-note" role="status">{message}</p> : null}
      <button className="button primary" type="submit" disabled={saving}>
        {saving ? 'Saving…' : 'Save settings'}
      </button>
    </form>
  );
}
