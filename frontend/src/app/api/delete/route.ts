import { NextRequest, NextResponse } from 'next/server';

const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';


export async function DELETE(request: NextRequest) {
  // Extract the ID from the request URL or search params
  const searchParams = request.nextUrl.searchParams;
  const id = searchParams.get('id');
  
  if (!id) {
    return NextResponse.json(
      { error: 'Event ID is required' },
      { status: 400 }
    );
  }


  try {
    const res = await fetch(`${apiURL}/events/${id}`, {
      method: 'DELETE',
    });

    if (!res.ok) {
      const err = await res.text();
      return NextResponse.json(
        { error: `Failed to delete event: ${err}` },
        { status: res.status }
      );
    }

    return NextResponse.json(
      { message: 'Event deleted successfully' },
      { status: 200 }
    );
  } catch (error) {
    console.error('DELETE error:', error);
    return NextResponse.json(
      { error: 'Server error' },
      { status: 500 }
    );
  }
}