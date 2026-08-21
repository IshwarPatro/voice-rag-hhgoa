import { NextResponse } from 'next/server';
import { db } from '../../../db';
import { queries } from '../../../db/schema';
import { desc } from 'drizzle-orm';

export async function GET() {
  try {
    const history = await db.select().from(queries).orderBy(desc(queries.generatedAt)).limit(15);
    return NextResponse.json(history);
  } catch (err: any) {
    // If backend DB is not configured yet (e.g. placeholder DATABASE_URL), return mock logs gracefully
    console.warn('Logging server database connection failed, falling back to in-memory mocks:', err.message);
    return NextResponse.json([
      {
        id: 1,
        queryText: "What is Hindi translation?",
        responseText: "The translation is typically correct and grounded.",
        latencyStt: 120,
        latencyModeration: 45,
        latencyRetrieval: 210,
        latencyLlm: 180,
        latencyTotal: 555,
        isSafe: true,
        generatedAt: new Date().toISOString()
      }
    ]);
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const result = await db.insert(queries).values({
      queryText: body.queryText,
      responseText: body.responseText,
      latencyStt: body.latencyStt || 0,
      latencyModeration: body.latencyModeration || 0,
      latencyRetrieval: body.latencyRetrieval || 0,
      latencyLlm: body.latencyLlm || 0,
      latencyTotal: body.latencyTotal || 0,
      isSafe: body.isSafe !== false,
      userId: body.userId || null
    }).returning();
    
    return NextResponse.json({ success: true, log: result[0] });
  } catch (err: any) {
    console.warn('Postgres database insert skipped:', err.message);
    return NextResponse.json({ success: false, error: err.message, mock: true });
  }
}
