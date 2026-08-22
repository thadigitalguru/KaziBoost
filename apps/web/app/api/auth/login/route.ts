import { NextResponse } from 'next/server';

const apiBaseUrl = (process.env.KAZIBOOST_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export async function POST(request: Request) {
  let payload: { email?: string; password?: string };
  try {
    payload = await request.json() as { email?: string; password?: string };
  } catch {
    return NextResponse.json({ detail: 'Invalid request body.', code: 'bad_request' }, { status: 400 });
  }

  if (!payload.email || !payload.password) {
    return NextResponse.json({ detail: 'Email and password are required.', code: 'bad_request' }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl}/v1/auth/login`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json({ detail: 'Authentication service is unavailable.', code: 'upstream_unavailable' }, { status: 502 });
  }

  const body = await upstream.json().catch(() => ({ detail: 'Authentication service returned an invalid response.' }));
  if (!upstream.ok) {
    return NextResponse.json(body, { status: upstream.status });
  }

  const responseBody = { ...body } as Record<string, unknown>;
  const accessToken = responseBody.access_token;
  if (typeof accessToken !== 'string' || accessToken.length === 0) {
    return NextResponse.json({ detail: 'Authentication service returned an invalid response.', code: 'upstream_invalid_response' }, { status: 502 });
  }
  delete responseBody.access_token;

  const response = NextResponse.json(responseBody);
  response.cookies.set('kaziboost_access_token', accessToken, {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60,
  });
  return response;
}
