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

---

## Setup & Installations

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Install Project Dependencies
Run the installation command in your local environment:
```bash
python -m pip install -r requirements.txt
```

### 3. Configure Credentials (.env)
Create a `.env` file in the project root directory and define the keys. (Optional/placeholders trigger local simulation/mock modes for cost-free developmental runs):
```env
SARVAM_API_KEY=your_sarvam_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

---

## Execution Guide

### Step 1: Ingest & Seed Database
Download the `ai4bharat/MSMARCO-XI` Hindi validation dataset, compute semantic splits, and populate the local vector database instance:
```bash
python retrieval/indexer.py
```
*Note: This will download files and save them to a local `local_qdrant/` catalog in the project root.*

### Step 2: Start the FastAPI Portal Server
Launch the unified server to host the APIs and serve the frontend dashboard portal:
```bash
PYTHONPATH=. uvicorn app:app --port 8000
```

### Step 3: Access the Voice-RAG Workspace
Open your web browser and navigate to:
```url
http://127.0.0.1:8000/
```

*   **Vocal Search**: Tap the glowing blue microphone icon, speak your Hindi geography or informational query, and tap again to stop.
*   **Text Search**: Click the "Or type your query" toggle link to reveal the text input pane, type your request (e.g. `एक कंपनी कहाँ निगमित होती है?`), and click **Execute Search**.

The dashboard will show real-time metrics, system statuses, latency budgets (SLA <200ms indicator), transcriptions, response logs, and matched database citations!

---

## Verification & Testing

### Running the Test Suite
Execute the automated validation suite measuring refusals, off-topics, safety issues, and groundedness rules:
```bash
PYTHONPATH=. pytest tests/
```

### Running Latency & Performance Diagnostics
Evaluate turnaround speed over **55 dataset queries** and print P50 / P70 / P90 / P99 percentiles:
```bash
PYTHONPATH=. python retrieval/latency_analytics.py
```
*Latency metrics are generated and saved to `metrics/latency_report.csv`.*
