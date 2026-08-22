import { cookies } from 'next/headers';

import type { AuthUser } from './api-client';

export type AuthTenant = {
  id: string;
  name: string;
};

export type CurrentAuthSession = {
  user: AuthUser;
  tenant: AuthTenant;
};

const apiBaseUrl = (process.env.KAZIBOOST_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export async function getCurrentAuthSession(): Promise<CurrentAuthSession | null> {
  const token = (await cookies()).get('kaziboost_access_token')?.value;
  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${apiBaseUrl}/v1/auth/me`, {
      headers: { authorization: `Bearer ${token}` },
      cache: 'no-store',
    });

    if (!response.ok) {
      return null;
    }

    return response.json() as Promise<CurrentAuthSession>;
  } catch {
    return null;
  }
}
