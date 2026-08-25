import { cookies } from 'next/headers';

export type OnboardingChecklist = {
  completed: number;
  total: number;
  items: Record<string, boolean>;
};

export type OnboardingRecommendation = {
  key: string;
  title: string;
  action: string;
};

export type DashboardSummary = {
  checklist: OnboardingChecklist;
  recommendations: OnboardingRecommendation[];
};

const apiBaseUrl = (process.env.KAZIBOOST_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export async function fetchDashboardSummary(): Promise<DashboardSummary | null> {
  const token = (await cookies()).get('kaziboost_access_token')?.value;
  if (!token) {
    return null;
  }

  try {
    const [checklistResponse, recommendationsResponse] = await Promise.all([
      fetch(`${apiBaseUrl}/v1/onboarding/checklist`, {
        headers: { authorization: `Bearer ${token}` },
        cache: 'no-store',
      }),
      fetch(`${apiBaseUrl}/v1/onboarding/recommendations`, {
        headers: { authorization: `Bearer ${token}` },
        cache: 'no-store',
      }),
    ]);

    if (!checklistResponse.ok || !recommendationsResponse.ok) {
      return null;
    }

    const [checklist, recommendations] = await Promise.all([
      checklistResponse.json() as Promise<OnboardingChecklist>,
      recommendationsResponse.json() as Promise<{ total: number; items: OnboardingRecommendation[] }>,
    ]);

    return { checklist, recommendations: recommendations.items };
  } catch {
    return null;
  }
}
