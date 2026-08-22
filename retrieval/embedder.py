import os
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class HuggingFaceEmbedder:
    """
    Lightweight wrapper that mimics the SentenceTransformer API.
    Rather than loading a 500MB PyTorch model in memory, it calls the remote 
    Hugging Face Inference API.
    """
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        if "/" not in model_name:
            model_name = f"sentence-transformers/{model_name}"
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.hf_token = os.getenv("HF_TOKEN")

    def encode(self, sentences, convert_to_numpy=True, **kwargs):
        # Handle both single string inputs and list of string inputs
        is_single = isinstance(sentences, str)
        inputs = [sentences] if is_single else sentences

        headers = {}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        try:
            # Standard Hugging Face Inference POST request
            response = requests.post(
                self.api_url,
                headers=headers,
                json={"inputs": inputs},
                timeout=12
            )
            response.raise_for_status()
            embeddings = response.json()

            # Sometimes HF Inference returns dict indicating loading or error (e.g. {"error": "..."})
            if isinstance(embeddings, dict) and "error" in embeddings:
                # If model is loading, it returning: {"error": "Model ... is currently loading", "estimated_time": 20.0}
                raise RuntimeError(f"HF API Error: {embeddings['error']}")

            # Convert response structure to NumPy array (shape: [num_sentences, 384])
            res = np.array(embeddings, dtype=np.float32)
            
            # If input was a single string, return a single shape [384] vector
            if is_single and len(res.shape) > 1:
                res = res[0]
            
            return res if convert_to_numpy else res.tolist()

        except Exception as e:
            # If remote request fails, try to fall back to a local SentenceTransformer model
            # (useful for offline local test environments that have the model cached).
            try:
                from sentence_transformers import SentenceTransformer
                print(f"HuggingFaceEmbedder warning: remote API request failed ({str(e)}). Falling back to offline SentenceTransformer.")
                if not hasattr(self, "_local_model"):
                    self._local_model = SentenceTransformer(self.model_name)
                
                res = self._local_model.encode(inputs, convert_to_numpy=True)
                if is_single and len(res.shape) > 1:
                    res = res[0]
                return res if convert_to_numpy else res.tolist()

            except ImportError:
                # If running on Render (without sentence-transformers installed), use deterministic pseudorandom fallback
                print(f"HuggingFaceEmbedder warning: remote API request failed ({str(e)}) and local libraries unavailable. Using deterministic mock.")
                fallback = []
                for s in inputs:
                    h = hash(s)
                    # Seed numpy locally to produce consistent vectors for queries
                    np.random.seed(h & 0xffffffff)
                    fallback.append(np.random.randn(384).astype(np.float32))

                res = np.array(fallback, dtype=np.float32)
                if is_single:
                    res = res[0]
                
                return res if convert_to_numpy else res.tolist()
