import { NextRequest } from 'next/server';

export async function GET(req: NextRequest) {
  const apiURL = process.env.NEXT_PUBLIC_API_URL;
  const paramMap = {
    search: "search",
    market: "market",
    industry: "industry",
    organizer: "organizer",
    valid: "valid",
    start_after: "start_after",
    start_before: "start_before",
    sort_by: "sort",
    sort_order: "order",
    limit: "limit",
    offset: "offset",
  };
  const params = new URLSearchParams();

  for (const [frontendKey, backendKey] of Object.entries(paramMap)) {
    const value = req.nextUrl.searchParams.get(frontendKey);
    if (value !== null && value !== undefined && value !== "") {
      params.set(backendKey, value);
    }
  }

  try {
    const res = await fetch(`${apiURL}/events?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!res.ok) {
      return new Response('Failed to fetch events', { status: res.status });
    }

    const data = await res.json();
    return Response.json(data);
  } catch (error) {
    console.error('API error:', error);
    return new Response('Server error', { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  const apiURL = process.env.NEXT_PUBLIC_API_URL;
  const body = await req.json();

  try {
    const res = await fetch(`${apiURL}/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errorData = await res.json();
      return new Response(JSON.stringify(errorData), { 
        status: res.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const data = await res.json();
    return Response.json(data);
  } catch (error) {
    console.error('API error:', error);
    return new Response('Server error', { status: 500 });
  }
}

// Update an event's information in the API
export async function PUT(request: NextRequest) {
  const apiURL = process.env.NEXT_PUBLIC_API_URL;

  try {
    const body = await request.json();

    // Destructure and exclude uneditable fields
    const { id, created_at, updated_at, ...updateData } = body;

    const res = await fetch(`${apiURL}/events/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    });

    if (!res.ok) {
      const errorData = await res.json();
      console.error('FastAPI error:', errorData);
      return new Response(JSON.stringify(errorData), {
        status: res.status,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const data = await res.json();
    return Response.json(data);
  } catch (error) {
    console.error('Next.js PUT error:', error);
    return new Response('Server error', { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  const apiURL = process.env.NEXT_PUBLIC_API_URL;
  const body = await req.json();

  try {
    const res = await fetch(`${apiURL}/events/${body.id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!res.ok) {
      return new Response('Failed to delete selected event', { status: res.status });
    }

    return new Response('Event deleted successfully', { status: 200 });
  } catch (error) {
    console.error('API error:', error);
    return new Response('Server error', { status: 500 });
  }
}