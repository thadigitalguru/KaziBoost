import { NextResponse } from 'next/server';

export async function POST() {
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
