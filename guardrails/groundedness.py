import numpy as np
from sentence_transformers import SentenceTransformer

class GroundednessChecker:
    def __init__(self, embedder=None):
        self.embedder = embedder or SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    def check_groundedness(self, answer, context_docs, threshold=0.55):
        """
        Computes maximum semantic similarity for each sentence in the answer
        against all sentences in the retrieved context documents.
        Returns (is_grounded, hallucinated_sentences).
        """
        if not answer or not context_docs:
            return True, []

        # If LLM explicitly refused
        if "CONTEXT_REFUSAL" in answer:
            return True, []

        # Parse sentences of the answer
        # Supports Hindi viram (।) and periods
        normalized_answer = answer.replace("।", ".").replace("\n", " ")
        ans_sentences = [s.strip() for s in normalized_answer.split(".") if s.strip()]
        if not ans_sentences:
            return True, []

        # Compile and parse all sentences in the context documents
        ctx_sentences = []
        for doc in context_docs:
            norm_ctx = doc['text'].replace("।", ".").replace("\n", " ")
            ctx_sentences.extend([s.strip() for s in norm_ctx.split(".") if s.strip()])

        if not ctx_sentences:
            return False, ans_sentences

        # Compute embeddings
        ans_embeddings = self.embedder.encode(ans_sentences, convert_to_numpy=True)
        ctx_embeddings = self.embedder.encode(ctx_sentences, convert_to_numpy=True)

        hallucinated = []
        
        # Norm context embeddings for vector multiplication
        ctx_norms = np.linalg.norm(ctx_embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        ctx_norms = np.where(ctx_norms == 0, 1e-9, ctx_norms)
        normalized_ctx = ctx_embeddings / ctx_norms

        for idx, ans_sent in enumerate(ans_sentences):
            ans_vec = ans_embeddings[idx]
            ans_norm = np.linalg.norm(ans_vec)
            if ans_norm == 0:
                continue

            # Compute similarities against all context sentences
            ans_vec_normalized = ans_vec / ans_norm
            similarities = np.dot(normalized_ctx, ans_vec_normalized)
            max_sim = float(np.max(similarities))

            if max_sim < threshold:
                hallucinated.append((ans_sent, max_sim))

        is_grounded = len(hallucinated) == 0
        return is_grounded, hallucinated
