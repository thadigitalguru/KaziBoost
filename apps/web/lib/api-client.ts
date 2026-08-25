export type AuthUser = {
  id: string;
  tenant_id: string;
  owner_name: string;
  email: string;
  role: string;
};

export type AuthSession = {
  access_token: string;
  token_type: string;
  user: AuthUser;
  tenant: { id: string; name: string };
};

export type AuthSessionResponse = Omit<AuthSession, 'access_token'>;

export type TenantSettingsProfile = {
  tenant: { id: string; name: string };
  user: AuthUser;
};

export type TenantSettingsUpdate = {
  business_name: string;
  owner_name: string;
};

export type SupportFeedback = {
  status: string;
  feedback_id: string;
};

export type SupportFeedbackInput = {
  page: string;
  message: string;
};

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code = 'api_error') {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => ({})) as { detail?: string; code?: string };
  if (!response.ok) {
    throw new ApiClientError(body.detail ?? 'The request could not be completed.', response.status, body.code);
  }
  return body as T;
}

export async function login(email: string, password: string): Promise<AuthSessionResponse> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return parseResponse<AuthSessionResponse>(response);
}

export async function logout(): Promise<void> {
  const response = await fetch('/api/auth/logout', { method: 'POST' });
  await parseResponse<{ status: string }>(response);
}

export async function fetchSettingsProfile(): Promise<TenantSettingsProfile> {
  const response = await fetch('/api/settings/profile', { cache: 'no-store' });
  return parseResponse<TenantSettingsProfile>(response);
}

export async function updateSettingsProfile(payload: TenantSettingsUpdate): Promise<TenantSettingsProfile> {
  const response = await fetch('/api/settings/profile', {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseResponse<TenantSettingsProfile>(response);
}

export async function submitFeedback(payload: SupportFeedbackInput): Promise<SupportFeedback> {
  const response = await fetch('/api/support/feedback', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseResponse<SupportFeedback>(response);
}
