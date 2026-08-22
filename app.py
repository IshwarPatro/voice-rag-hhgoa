import os
# RAM-saving thread-pool limit rules for PyTorch & CPU scaling
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TORCH_NUM_THREADS"] = "1"

import shutil
import tempfile
try:
    import torch
    # Restrict torch computation concurrency overhead if installed
    torch.set_num_threads(1)
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from harness.engine import VoiceRAGEngine

app = FastAPI(title="Voice-RAG for MSMARCO-XI", version="1.0.0")

# Enable CORS for the premium frontend portal
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global engine once to share across requests
print("Pre-loading VoiceRAGEngine in FastAPI app server...")
engine = VoiceRAGEngine()

@app.get("/", response_class=HTMLResponse)
def serve_portal():
    """
    Serves the portal workspace control dashboard.
    """
    try:
        portal_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
        with open(portal_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return HTMLResponse(content=f"<h3>Portal Loading Failed: {str(e)}</h3>", status_code=500)

@app.get("/gini.png")
def serve_logo():
    logo_path = os.path.join(os.path.dirname(__file__), "frontend", "gini.png")
    return FileResponse(logo_path)

@app.get("/gini_favicon.png")
def serve_favicon():
    fav_path = os.path.join(os.path.dirname(__file__), "frontend", "gini_favicon.png")
    return FileResponse(fav_path)

class QueryRequest(BaseModel):
    query: str
    language_code: str = "hi-IN"

@app.post("/api/query")
def run_text_query(req: QueryRequest):
    """
    Exposes dry-run query pipeline over direct text inputs.
    """
    try:
        result = engine.pipeline_run(query_text=req.query, language_code=req.language_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice")
def run_voice_query(
    file: UploadFile = File(...),
    language_code: str = Form("hi-IN")
):
    """
    Receives voice wav files from browser recorder and executes speech RAG.
    """
    # Write uploaded stream to temporary file on disk for the transcriber
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name

    try:
        result = engine.pipeline_run(audio_path=tmp_path, language_code=language_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "voice-rag-engine"}
