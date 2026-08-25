import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const apiBaseUrl = (process.env.KAZIBOOST_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

async function proxy(request: Request, method: 'GET' | 'PUT') {
  const token = (await cookies()).get('kaziboost_access_token')?.value;
  if (!token) {
    return NextResponse.json({ detail: 'Not authenticated.', code: 'unauthorized' }, { status: 401 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl}/v1/settings/profile`, {
      method,
      headers: {
        authorization: `Bearer ${token}`,
        ...(method === 'PUT' ? { 'content-type': 'application/json' } : {}),
      },
      body: method === 'PUT' ? await request.text() : undefined,
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json({ detail: 'Settings service is unavailable.', code: 'upstream_unavailable' }, { status: 502 });
  }

  const body = await upstream.json().catch(() => ({ detail: 'Settings service returned an invalid response.' }));
  return NextResponse.json(body, { status: upstream.status });
}

export async function GET(request: Request) {
  return proxy(request, 'GET');
}

export async function PUT(request: Request) {
  return proxy(request, 'PUT');
}
