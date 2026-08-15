export type Readiness = {
  status: 'ready' | 'not_ready' | string;
  checks: Record<string, string>;
};

const apiBaseUrl = (process.env.KAZIBOOST_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export async function fetchReadiness(): Promise<Readiness> {
  const response = await fetch(`${apiBaseUrl}/ready`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`API readiness request failed with status ${response.status}`);
  }
  return response.json() as Promise<Readiness>;
}
