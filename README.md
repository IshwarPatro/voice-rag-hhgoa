# Voice-RAG system for MSMARCO-XI

A high-performance, voice-enabled Retrieval-Augmented Generation (RAG) system targeting the `ai4bharat/MSMARCO-XI` dataset with a strict sub-200ms latency profile. Built with FastAPI, Qdrant, Sarvam AI STT, and Groq LLM.

---

## Project Structure

```text
├── app.py                   # FastAPI REST backend and frontend portal server
├── requirements.txt         # Project package dependencies
├── README.md                # This instruction guide
├── stt/
│   └── transcriber.py       # Sarvam AI transcription client wrapper
├── retrieval/
│   ├── indexer.py           # MSMARCO-XI dataset ingester & Qdrant database seeder
│   ├── searcher.py          # Qdrant client vector index search orchestrator
│   └── latency_analytics.py # Performance analytics suite running 50+ batch queries
├── generation/
│   └── generator.py         # Groq LLM completion engine wrapper
├── guardrails/
│   ├── moderation.py        # Malicious and off-topic domain classifiers
│   └── groundedness.py      # Semantic hallucination verification check
├── harness/
│   └── engine.py            # Central pipeline orchestrator
├── tests/
│   ├── test_guardrails.py   # Guardrails assertions tests
│   └── test_harness.py      # Pipeline routing verification tests
└── frontend/
    └── index.html           # Ambient, premium glassmorphism assistant interface
```

## Setup & Installations

### 1. Prerequisites
Ensure Python 3.10+ and Node.js 18+ are installed on your system.

### 2. Install Project Dependencies
Run the installation command in your local environment:
```bash
python -m pip install -r requirements.txt
```

Inside the `portal` directory, install Next.js frontend packages:
```bash
cd portal
npm install
```

### 3. Configure Credentials (.env)
Create a `.env` file in the project root directory:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
HF_TOKEN=your_huggingface_api_token_here
```
*(Optional/placeholders trigger local simulation/mock modes for cost-free developmental runs)*

Configure the database credentials for logging inside `portal/.env`:
```env
DATABASE_URL=postgres://username:password@your-database-host:5432/voicerag?sslmode=require
NEXTAUTH_SECRET=a_random_32_character_string
```

---

## Execution Guide

To run the complete Voice-RAG system, you will need to run the **FastAPI backend** (ML processing engine) and the **Next.js frontend portal** side-by-side.

### Step 1: Ingest & Seed Database
Download the `ai4bharat/MSMARCO-XI` Hindi validation dataset, compute semantic splits, and populate the local Qdrant collection:
```bash
python retrieval/indexer.py
```
*Note: This will download files and save them to a local `local_qdrant/` catalog in the project root.*

### Step 2: Start the FastAPI Backend Engine
Launch the Python orchestration engine uvicorn server in your first terminal session:
```bash
PYTHONPATH=. uvicorn app:app --port 8000
```

### Step 3: Run the Next.js Frontend Portal
Open a new terminal window, navigate to the `portal/` subdirectory, and boot up the visual dashboard website:
```bash
cd portal
npm run dev
```

### Step 4: Access the Voice-RAG Workspace
Open your web browser and navigate to:
```url
http://localhost:3000
```
*Login using client sessions (Credentials are validated via NextAuth)*

---

## Verification & Testing

### Running the Test Suite
Execute the automated validation suite measuring safety filters, off-topics, and groundedness rules:
```bash
PYTHONPATH=. pytest tests/
```

### Running Latency & Performance Diagnostics
Evaluate turnaround speed over **55 dataset queries** and print P50 / P70 / P90 / P99 percentiles:
```bash
PYTHONPATH=. python retrieval/latency_analytics.py
```
*Latency metrics are generated and saved to `metrics/latency_report.csv`.*

