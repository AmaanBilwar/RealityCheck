import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const { message } = await request.json();

  // Here you would typically send the message to your FastAPI backend
  const response = await fetch(`${process.env.BACKEND_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    return NextResponse.json({ error: 'Failed to send message' }, { status: 500 });
  }

  const data = await response.json();
  return NextResponse.json(data);
}