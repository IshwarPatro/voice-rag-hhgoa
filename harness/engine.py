import os
import time
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from stt.transcriber import SarvamTranscriber
from retrieval.searcher import VectorSearcher
from generation.generator import LLMGenerator
from guardrails.moderation import ModerationShield
from guardrails.groundedness import GroundednessChecker

DB_PATH = "local_qdrant"

class VoiceRAGEngine:
    def __init__(self):
        # 1. Share resources (Model and DB Client) to save RAM and initialization latency
        print("Initializing SentenceTransformer and Qdrant DB connection in Orchestrator Engine...")
        self.shared_embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.shared_db_client = QdrantClient(path=DB_PATH)
        
        # 2. Instantiate individual modular units
        self.transcriber = SarvamTranscriber()
        self.searcher = VectorSearcher(embedder=self.shared_embedder, client=self.shared_db_client)
        self.generator = LLMGenerator()
        self.moderator = ModerationShield()
        self.groundedness = GroundednessChecker(embedder=self.shared_embedder)

    def pipeline_run(self, audio_path=None, query_text=None, language_code="hi-IN"):
        """
        Coordinates the Voice-RAG execution flow, reporting step-by-step performance latencies.
        """
        latencies = {
            "stt": 0.0,
            "moderation": 0.0,
            "retrieval": 0.0,
            "generation": 0.0,
            "groundedness": 0.0,
            "total": 0.0
        }
        
        total_start = time.perf_counter()
        
        # Step 1: Speech to Text (if audio path supplied)
        query = query_text
        if audio_path:
            stt_start = time.perf_counter()
            try:
                query = self.transcriber.transcribe(audio_path, language_code=language_code)
                latencies["stt"] = round((time.perf_counter() - stt_start) * 1000, 2)
            except Exception as e:
                latencies["stt"] = round((time.perf_counter() - stt_start) * 1000, 2)
                latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
                return {
                    "query": "",
                    "answer": f"Speech conversion pipeline error: {str(e)}",
                    "context": [],
                    "status": "ERROR_STT",
                    "latency": latencies
                }
        
        if not query:
            latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
            return {
                "query": "",
                "answer": "No input query provided.",
                "context": [],
                "status": "ERROR_EMPTY_INPUT",
                "latency": latencies
            }

        # Step 2: Content Moderation & Off-topic Filters
        mod_start = time.perf_counter()
        is_safe, safety_reason = self.moderator.is_safe(query)
        if not is_safe:
            latencies["moderation"] = round((time.perf_counter() - mod_start) * 1000, 2)
            latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
            return {
                "query": query,
                "answer": f"Unsafe query refused. Reason: {safety_reason}",
                "context": [],
                "status": "REJECTED_SAFETY",
                "latency": latencies
            }

        is_topic, topic_reason = self.moderator.is_on_topic(query)
        if not is_topic:
            latencies["moderation"] = round((time.perf_counter() - mod_start) * 1000, 2)
            latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
            return {
                "query": query,
                "answer": f"I'm sorry, that is off-topic. {topic_reason}",
                "context": [],
                "status": "REJECTED_TOPIC",
                "latency": latencies
            }
        latencies["moderation"] = round((time.perf_counter() - mod_start) * 1000, 2)

        # Step 3: Document Retrieval from Vector DB
        ret_start = time.perf_counter()
        try:
            # Score threshold of 0.55 matches our search config
            matched_docs = self.searcher.search(query, limit=3, score_threshold=0.55)
            latencies["retrieval"] = round((time.perf_counter() - ret_start) * 1000, 2)
        except Exception as e:
            latencies["retrieval"] = round((time.perf_counter() - ret_start) * 1000, 2)
            latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
            return {
                "query": query,
                "answer": f"Vector indexing retrieval failure: {str(e)}",
                "context": [],
                "status": "ERROR_RETRIEVAL",
                "latency": latencies
            }

        # Step 4: Refusal-on-no-context (Skip LLM generation completely if score is poor)
        if not matched_docs:
            latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
            return {
                "query": query,
                "answer": "मुझे क्षमा करें, लेकिन प्रदान किए गए दस्तावेजों में इसका उत्तर नहीं मिला। (Refusal: No relevant context in files.)",
                "context": [],
                "status": "REFUSAL_NO_CONTEXT",
                "latency": latencies
            }

        # Step 5: Answer Generation
        gen_start = time.perf_counter()
        try:
            answer = self.generator.generate(query, matched_docs)
            latencies["generation"] = round((time.perf_counter() - gen_start) * 1000, 2)
        except Exception as e:
            latencies["generation"] = round((time.perf_counter() - gen_start) * 1000, 2)
            latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
            return {
                "query": query,
                "answer": f"LLM content compilation error: {str(e)}",
                "context": matched_docs,
                "status": "ERROR_GENERATION",
                "latency": latencies
            }

        # Step 6: Refusal-on-no-context from system output flag
        if answer == "CONTEXT_REFUSAL":
            latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
            return {
                "query": query,
                "answer": "मुझे क्षमा करें, लेकिन प्रदान किए गए दस्तावेजों में इसका उत्तर नहीं मिला। (Refusal: No relevant context in files.)",
                "context": matched_docs,
                "status": "REFUSAL_NO_CONTEXT",
                "latency": latencies
            }

        # Step 7: Groundedness & Hallucination Guardrail Check
        grd_start = time.perf_counter()
        is_grounded, hallucinated_parts = self.groundedness.check_groundedness(answer, matched_docs)
        latencies["groundedness"] = round((time.perf_counter() - grd_start) * 1000, 2)

        if not is_grounded:
            latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
            # Override answer with refusal to avoid hallucinating
            print(f"Hallucination Warning! Generated sentence failed validation: {hallucinated_parts}")
            return {
                "query": query,
                "answer": "मुझे क्षमा करें, लेकिन मैं केवल प्रदान किए गए दस्तावेजों के अनुसार ही उत्तर दे सकता हूँ। (Refusal: Generated answer failed groundedness validation.)",
                "context": matched_docs,
                "status": "REJECTED_GROUNDEDNESS",
                "latency": latencies
            }

        latencies["total"] = round((time.perf_counter() - total_start) * 1000, 2)
        return {
            "query": query,
            "answer": answer,
            "context": matched_docs,
            "status": "SUCCESS",
            "latency": latencies
        }
