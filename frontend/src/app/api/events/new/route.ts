import { NextRequest } from 'next/server';

const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';

export async function POST(req: NextRequest) {

  try {
    const body = await req.json();

    const res = await fetch(`${apiURL}/events/new`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      return new Response('Failed to create event', { status: res.status });
    }

    const data = await res.json();
    return Response.json(data);
  } catch (error) {
    console.error('Manual event POST error:', error);
    return new Response('Internal server error', { status: 500 });
  }
}
