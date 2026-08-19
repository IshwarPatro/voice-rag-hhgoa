import os
import sys
import time
import numpy as np
import pandas as pd
from harness.engine import VoiceRAGEngine

def run_performance_test():
    print("Initializing Voice-RAG Engine...")
    engine = VoiceRAGEngine()
    
    # Let's load 60 sample queries from validation parquet or define a list of test queries
    # To be extremely fast and robust, let's load actual questions from the database.
    # We can fetch first 60 queries from the validation dataset to perform real retrieval and generation.
    url = "https://huggingface.co/datasets/ai4bharat/MSMARCO-XI/resolve/main/validation/hinval.parquet"
    print("Loading test queries from validation dataset...")
    try:
        df = pd.read_parquet(url, engine='pyarrow')
        df = df[df['query'].notna() & df['passages'].notna()]
        test_rows = df.head(55)
    except Exception as e:
        print(f"Error loading parquet queries: {e}. Falling back to syntax queries.")
        # Fallback queries if network issue
        test_rows = pd.DataFrame({
            "query": [
                "एक कंपनी कहाँ निगमित होती है?",
                "बी कोर समुदाय में कितने संगठन हैं?",
                "सुरक्षा बाईपास के तरीके क्या हैं?", # unsafe
                "How to write python decorator class code?", # offtopic
            ] * 15
        })

    queries = test_rows['query'].tolist()
    print(f"Evaluating {len(queries)} evaluation queries...")
    
    results = []
    
    for idx, q in enumerate(queries):
        start = time.perf_counter()
        # Run end-to-end pipeline
        res = engine.pipeline_run(query_text=q)
        duration_ms = (time.perf_counter() - start) * 1000
        
        step_latencies = res.get("latency", {})
        results.append({
            "query": q,
            "status": res["status"],
            "stt": step_latencies.get("stt", 0.0),
            "moderation": step_latencies.get("moderation", 0.0),
            "retrieval": step_latencies.get("retrieval", 0.0),
            "generation": step_latencies.get("generation", 0.0),
            "groundedness": step_latencies.get("groundedness", 0.0),
            "total_measured": round(duration_ms, 2)
        })
        
        if (idx + 1) % 10 == 0:
            print(f"Processed {idx + 1}/{len(queries)} queries...")

    # Calculate percentiles
    df_results = pd.DataFrame(results)
    
    print("\n================ LATENCY RESULTS PERFORMANCE REPORT ================")
    print(f"Total Queries Evaluated: {len(df_results)}")
    print(f"Successful Runs: {len(df_results[df_results['status'] == 'SUCCESS'])}")
    print(f"Off-Topic Rejections: {len(df_results[df_results['status'] == 'REJECTED_TOPIC'])}")
    print(f"Unsafe Rejections: {len(df_results[df_results['status'] == 'REJECTED_SAFETY'])}")
    print(f"Refusal No Context: {len(df_results[df_results['status'] == 'REFUSAL_NO_CONTEXT'])}")
    print(f"Rejected Groundedness: {len(df_results[df_results['status'] == 'REJECTED_GROUNDEDNESS'])}")
    
    metrics = ["stt", "moderation", "retrieval", "generation", "groundedness", "total_measured"]
    
    summary_data = []
    for metric in metrics:
        data = df_results[metric]
        p50 = np.percentile(data, 50)
        p70 = np.percentile(data, 70)
        p90 = np.percentile(data, 90)
        p99 = np.percentile(data, 99)
        p100 = np.percentile(data, 100)
        summary_data.append({
            "Metric": metric.upper(),
            "P50 (ms)": f"{p50:.2f}",
            "P70 (ms)": f"{p70:.2f}",
            "P90 (ms)": f"{p90:.2f}",
            "P99 (ms)": f"{p99:.2f}",
            "Max/P100 (ms)": f"{p100:.2f}"
        })
        
    df_sum = pd.DataFrame(summary_data)
    print("\n", df_sum.to_string(index=False))
    print("====================================================================")

    # Save to CSV for walkthrough records
    os.makedirs("metrics", exist_ok=True)
    df_results.to_csv("metrics/latency_report.csv", index=False)
    print("Saved report to metrics/latency_report.csv")

if __name__ == "__main__":
    run_performance_test()
