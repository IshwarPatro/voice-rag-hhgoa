import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "msmarco_xi")
DB_PATH = "local_qdrant"

class VectorSearcher:
    def __init__(self, embedder=None, client=None):
        # Allow passing existing instances to reduce memory load
        self.embedder = embedder or SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        if client:
            self.client = client
        else:
            qdrant_host = os.getenv("QDRANT_HOST", "localhost")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            if qdrant_host.startswith("http://") or qdrant_host.startswith("https://") or qdrant_api_key:
                self.client = QdrantClient(
                    url=qdrant_host,
                    api_key=qdrant_api_key
                )
            elif qdrant_host != "localhost":
                self.client = QdrantClient(
                    host=qdrant_host,
                    port=int(os.getenv("QDRANT_PORT", "6333")),
                    api_key=qdrant_api_key
                )
            else:
                self.client = QdrantClient(path=DB_PATH)

    def search(self, query_text, limit=3, score_threshold=0.55):
        """
        Encodes query_text, searches child/parent nodes in Qdrant,
        and returns matched parent contexts with scores.
        """
        # Encode query
        query_vector = self.embedder.encode(query_text).tolist()
        
        # Query Qdrant
        results = self.client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            limit=limit
        ).points

        matched_docs = []
        seen_parent_ids = set()

        for res in results:
            if res.score < score_threshold:
                continue

            payload = res.payload
            parent_id = payload.get("parent_id")
            
            # De-duplicate parent passages
            if parent_id in seen_parent_ids:
                continue
                
            seen_parent_ids.add(parent_id)

            # Retrieve text (depends on whether matched node is parent or child)
            # If child, we get payload["parent_text"]. Otherwise payload["text"].
            passage_text = payload.get("parent_text") if payload.get("type") == "child" else payload.get("text")
            
            matched_docs.append({
                "passage_id": parent_id,
                "text": passage_text,
                "score": res.score,
                "is_ground_truth": payload.get("is_ground_truth", 0),
                "source_lang": payload.get("source_lang", "en"),
                "target_lang": payload.get("target_lang", "hi")
            })

        return matched_docs
