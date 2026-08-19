import os
import sys
import pandas as pd
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load env file paths
load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "msmarco_xi")

# Path for in-memory / file-backed persistent storage to avoid requiring Docker
DB_PATH = "local_qdrant"

def get_qdrant_client():
    """
    Returns a Qdrant client. First tries local directory persistent DB,
    falling back to standard port-based client if configuration dictates.
    """
    print(f"Initializing Qdrant client at local directory: '{DB_PATH}'...")
    return QdrantClient(path=DB_PATH)

def load_indic_dataset(limit=50):
    """
    Downloads and loads a chunk of the Hindi MSMARCO-XI validation subset.
    """
    url = "https://huggingface.co/datasets/ai4bharat/MSMARCO-XI/resolve/main/validation/hinval.parquet"
    print(f"Downloading training split from AI4Bharat: {url} (Loading first {limit} records)...")
    try:
        # Load parquet file into memory
        df = pd.read_parquet(url, engine='pyarrow')
        # Filter for rows that actually have passages
        df = df[df['passages'].notna()]
        return df.head(limit)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

def semantic_sentence_split(text):
    """
    Splits text into sentences. Simple rule-based splitter that handles Hindi purna viram (।) and English periods.
    """
    # Replace Hindi sentence ending with period to split easily
    normalized = text.replace("।", ".").replace("\n", " ")
    sentences = [s.strip() for s in normalized.split(".") if s.strip()]
    return sentences

class MultistrategyChunker:
    def __init__(self, embedder):
        self.embedder = embedder

    def chunk_fixed_sliding(self, text, size=80, overlap=20):
        """
        Naive fixed token/word sliding window chunker.
        """
        words = text.split()
        if len(words) <= size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(words):
            end = start + size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            start += (size - overlap)
        return chunks

    def chunk_semantic(self, text, similarity_threshold=0.6):
        """
        Computes sentence embeddings and groups sentences into chunks
        when the semantic similarity between consecutive sentences drops.
        """
        sentences = semantic_sentence_split(text)
        if len(sentences) <= 1:
            return sentences

        # Compute embeddings for sentences
        embeddings = self.embedder.encode(sentences, convert_to_numpy=True)
        
        chunks = []
        current_chunk = [sentences[0]]
        
        for idx in range(1, len(sentences)):
            # Calculate cosine similarity between consecutive sentences
            vec1 = embeddings[idx - 1]
            vec2 = embeddings[idx]
            
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 > 0 and norm2 > 0:
                sim = np.dot(vec1, vec2) / (norm1 * norm2)
            else:
                sim = 0.0
                
            if sim >= similarity_threshold:
                current_chunk.append(sentences[idx])
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[idx]]
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

def seed_database():
    # 1. Load embedding model
    print("Loading multilingual sentence embedding model (paraphrase-multilingual-MiniLM-L12-v2)...")
    embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    embedding_dim = 384  # MiniLM dimension
    
    # 2. Load dataset records
    df = load_indic_dataset(limit=100)
    
    # 3. Connect to Qdrant
    client = get_qdrant_client()
    
    # Recreate collection
    print(f"Creating collection '{QDRANT_COLLECTION}' in Qdrant...")
    client.recreate_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=models.VectorParams(
            size=embedding_dim,
            distance=models.Distance.COSINE
        )
    )
    
    chunker = MultistrategyChunker(embedder)
    points = []
    point_id_counter = 1
    
    print("Processing documents & chunking...")
    for idx, row in df.iterrows():
        query_id = int(row['query_id'])
        target_lang = row['target_lang']
        source_lang = row['source_lang']
        
        passages_data = row['passages']
        if not passages_data or 'Translated_passages' not in passages_data:
            continue
            
        translated_passages = passages_data['Translated_passages']
        is_selected_flags = passages_data['is_selected']
        
        for p_idx, text in enumerate(translated_passages):
            if not text:
                continue
            
            # Ground truth flag: does this passage contain the target answer?
            is_ground_truth = int(is_selected_flags[p_idx]) if p_idx < len(is_selected_flags) else 0
            
            # 1. Create Parent Chunk (full passage context for indexing metadata query response)
            parent_text = text
            parent_vector = embedder.encode(parent_text).tolist()
            
            # 2. Extract semantic chunks (Child Chunks)
            semantic_child_texts = chunker.chunk_semantic(parent_text, similarity_threshold=0.55)
            
            # 3. Add parent node to index
            parent_point_id = point_id_counter
            points.append(models.PointStruct(
                id=parent_point_id,
                vector=parent_vector,
                payload={
                    "text": parent_text,
                    "type": "parent",
                    "parent_id": parent_point_id, # Self referential since it is the parent
                    "query_id": query_id,
                    "target_lang": target_lang,
                    "source_lang": source_lang,
                    "is_ground_truth": is_ground_truth,
                    "passage_idx": p_idx
                }
            ))
            point_id_counter += 1
            
            # 4. Add child nodes to index, referencing their parent node
            for child_idx, child_text in enumerate(semantic_child_texts):
                child_vector = embedder.encode(child_text).tolist()
                points.append(models.PointStruct(
                    id=point_id_counter,
                    vector=child_vector,
                    payload={
                        "text": child_text,
                        "type": "child",
                        "parent_text": parent_text, # Embed full parent context reference inside payload
                        "parent_id": parent_point_id,
                        "query_id": query_id,
                        "target_lang": target_lang,
                        "source_lang": source_lang,
                        "is_ground_truth": is_ground_truth,
                        "passage_idx": p_idx,
                        "child_idx": child_idx
                    }
                ))
                point_id_counter += 1
                
    print(f"Uploading {len(points)} vector chunks to Qdrant collection...")
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points
    )
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
