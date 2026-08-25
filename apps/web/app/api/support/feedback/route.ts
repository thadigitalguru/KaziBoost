import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const apiBaseUrl = (process.env.KAZIBOOST_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export async function POST(request: Request) {
  const token = (await cookies()).get('kaziboost_access_token')?.value;
  if (!token) {
    return NextResponse.json({ detail: 'Not authenticated.', code: 'unauthorized' }, { status: 401 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl}/v1/support/feedback`, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${token}`,
        'content-type': 'application/json',
      },
      body: await request.text(),
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json({ detail: 'Feedback service is unavailable.', code: 'upstream_unavailable' }, { status: 502 });
  }

  const body = await upstream.json().catch(() => ({ detail: 'Feedback service returned an invalid response.' }));
  return NextResponse.json(body, { status: upstream.status });
}
