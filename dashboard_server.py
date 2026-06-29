from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import json
import pandas as pd
import os

app = FastAPI(title="RAG Evaluation Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return FileResponse("dashboard.html")

@app.get("/api/evaluation-data")
async def get_evaluation_data():
    """Load and return evaluation data"""
    try:
        # Find the most recent judge results file
        judge_files = [f for f in os.listdir('.') if f.startswith('rag_eval_judge_summary_') and f.endswith('.csv')]
        if not judge_files:
            raise HTTPException(status_code=404, detail="No evaluation data found")
        
        latest_file = sorted(judge_files)[-1]
        df = pd.read_csv(latest_file)
        
        # Calculate overall metrics
        total = len(df)
        successful = len(df[~df['has_error']])
        
        # Judge scores
        judge_scores = {
            "overall": df['judge_overall'].mean(),
            "correctness": df['judge_correctness'].mean(),
            "completeness": df['judge_completeness'].mean(),
            "relevance": df['judge_relevance'].mean(),
            "retrieval_quality": df['judge_retrieval'].mean(),
            "hallucination_check": df['judge_hallucination'].mean()
        }
        
        # Document stats
        doc_stats = []
        for doc in df['document'].unique():
            doc_df = df[df['document'] == doc]
            doc_stats.append({
                "name": doc,
                "count": len(doc_df),
                "overall_score": doc_df['judge_overall'].mean(),
                "correctness": doc_df['judge_correctness'].mean(),
                "retrieval": doc_df['judge_retrieval'].mean()
            })
        
        # Score distribution
        score_dist = {
            "excellent": len(df[df['judge_overall'] >= 4]),
            "good": len(df[(df['judge_overall'] >= 3) & (df['judge_overall'] < 4)]),
            "fair": len(df[(df['judge_overall'] >= 2) & (df['judge_overall'] < 3)]),
            "poor": len(df[df['judge_overall'] < 2])
        }
        
        # Prepare results for table
        results = df.to_dict('records')
        
        return JSONResponse({
            "total": total,
            "successful": successful,
            "successRate": round((successful / total) * 100, 1),
            "avgResponseTime": int(df['response_time_ms'].mean()),
            "totalCost": df['cost_usd'].sum(),
            "avgCostPerQuery": df['cost_usd'].mean(),
            "judgeScores": judge_scores,
            "docStats": doc_stats,
            "scoreDistribution": score_dist,
            "results": results
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
