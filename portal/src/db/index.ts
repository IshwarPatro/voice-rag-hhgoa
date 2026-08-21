import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const connectionString = process.env.DATABASE_URL || 'postgresql://localhost:5432/voicerag';

// Disable TLS issues if connecting on local/Neon databases
const client = postgres(connectionString, { ssl: connectionString.includes('neon.tech') ? 'require' : false });
export const db = drizzle(client, { schema });
