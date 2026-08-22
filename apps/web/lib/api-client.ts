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
