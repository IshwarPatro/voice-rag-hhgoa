---
description: How to deploy the Voice-RAG portal stack to production
---

# Deploying the Voice-RAG Stack to Production

The Voice-RAG system consists of three parts that need to be deployed:
1. **Database Logs**: Supabase PostgreSQL DB (already hosted on Supabase Cloud).
2. **Backend**: Python FastAPI Server + Qdrant Vector Storage.
3. **Frontend**: Next.js Visual Dashboard.

Follow these step-by-step instructions to host the backend and database.

---

## Step 1: Set Up Qdrant Cloud (Free Vector database)

In production, local file-based Qdrant isn't persistent on platforms like Render or Vercel. We will host the vectors on Qdrant Cloud.

1. **Sign up**: Visit [https://cloud.qdrant.io](https://cloud.qdrant.io) and create a free account.
2. **Create Cluster**: Select **Create Cluster** (Free Tier - 1GB RAM, 0.5 CPU is more than enough for our ~4,300 vectors).
3. **Save API Key & URL**:
   * Copy the **Cluster URL** (e.g., `https://xxxxxx-xxxx-xxxx.gcp.qdrant.io`).
   * Copy the **API Key** generated when creating the cluster.
4. **Seed data to Qdrant Cloud (Optional)**:
   * To upload your indexed nodes to your new cloud database, edit your local `.env` with:
     ```env
     QDRANT_HOST=https://xxxxxx-xxxx-xxxx.gcp.qdrant.io
     QDRANT_API_KEY=your-api-key
     QDRANT_PORT=6333
     ```
   * Run the indexer script to seed vectors:
     ```bash
     PYTHONPATH=. python retrieval/indexer.py
     ```

---

## Step 2: Deploy FastAPI Backend (on Render.com)

We will host the Python server on Render's free tier.

1. **Connect GitHub**: Sign into [https://render.com](https://render.com) and link your GitHub account.
2. **New Web Service**: Click **New +** $\rightarrow$ **Web Service**.
3. **Choose Repository**: Select your Hacker House repository.
4. **Configure Settings**:
   * **Runtime**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn app:app --host 0.0.0.0 --port 10000` (Render binds to port `10000` automatically)
5. **Add Environment Variables**: Under the **Environment** tab, click **Add Environment Variable**:
   * `HF_TOKEN` = `your-huggingface-token`
   * `SARVAM_API_KEY` = `saaras-api-key`
   * `QDRANT_HOST` = `https://xxxxxx-xxxx-xxxx.gcp.qdrant.io`
   * `QDRANT_API_KEY` = `your-api-key`
   * `QDRANT_PORT` = `6333`
   * `QDRANT_COLLECTION` = `msmarco_xi`
6. **Deploy**: Render will build the image and output a live backend URL (e.g. `https://hacker-house-stt-backend.onrender.com`).

---

## Step 3: Deploy Next.js Frontend (on Vercel)

Next.js operates as our primary visual client, connecting to our Render backend API and Supabase logging DB.

1. **New Vercel Project**: Go to [https://vercel.com](https://vercel.com) and click **Add New** $\rightarrow$ **Project**.
2. **Import Repository**: Select your GitHub repository.
3. **Configure Settings**:
   * **Root Directory**: Select `portal` (this path is highly important!).
   * **Framework Preset**: `Next.js`
4. **Environment Variables**: Add these exact keys:
   * `NEXT_PUBLIC_BACKEND_URL` = `https://hacker-house-stt-backend.onrender.com` (your Render URL from Step 2)
   * `DATABASE_URL` = `your-supabase-postgres-connection-string` (for logging)
   * `NEXT_PUBLIC_SUPABASE_URL` = `your-supabase-api-url`
   * `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` = `your-supabase-anon-key`
   * `NEXTAUTH_SECRET` = `any-random-base64-string`
5. **Deploy**: Click deploy. Vercel will build of Next.js and give you a public URL (e.g. `https://gini-rag-portal.vercel.app`).
