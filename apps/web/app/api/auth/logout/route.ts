import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const apiBaseUrl = (process.env.KAZIBOOST_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export async function POST() {
  const token = (await cookies()).get('kaziboost_access_token')?.value;

  if (token) {
    try {
      await fetch(`${apiBaseUrl}/v1/auth/logout`, {
        method: 'POST',
        headers: { authorization: `Bearer ${token}` },
        cache: 'no-store',
      });
    } catch {
      // Clear the local session cookie even if the upstream service is unavailable.
    }
  }

  const response = NextResponse.json({ status: 'logged_out' });
  response.cookies.set('kaziboost_access_token', '', {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 0,
  });
  return response;
}
