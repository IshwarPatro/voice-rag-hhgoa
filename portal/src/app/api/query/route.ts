import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const contentType = req.headers.get('content-type') || '';
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
    
    if (contentType.includes('application/json')) {
      const body = await req.json();
      const response = await fetch(`${BACKEND_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      
      const data = await response.json();
      return NextResponse.json(data);
    }
    
    if (contentType.includes('multipart/form-data')) {
      const formData = await req.formData();
      
      // Target correct multipart post to FastAPI app (VoiceRAGEngine)
      const response = await fetch(`${BACKEND_URL}/api/voice`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      return NextResponse.json(data);
    }
    
    return NextResponse.json({ error: 'Unsupported Content-Type' }, { status: 400 });
  } catch (err: any) {
    console.error('API Error Proxying to FastAPI:', err);
    return NextResponse.json({ 
      error: 'FastAPI Backend Engine Connection Failed', 
      details: err.message 
    }, { status: 502 });
  }
}
