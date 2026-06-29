import json
import requests
import time
from datetime import datetime
from typing import List, Dict
import pandas as pd

class RAGEvaluator:
    def __init__(self, api_url: str, qa_file: str):
        self.api_url = api_url
        self.qa_file = qa_file
        self.results = []
    
    def load_qa_pairs(self) -> List[Dict]:
        """Load Q&A pairs from JSON file"""
        with open(self.qa_file, 'r') as f:
            return json.load(f)
    
    def query_rag(self, question: str) -> Dict:
        """Query the RAG system"""
        try:
            response = requests.post(
                f"{self.api_url}/query",
                json={"question": question},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "answer": ""}
        except Exception as e:
            return {"error": str(e), "answer": ""}
    
    def calculate_metrics(self, expected: str, actual: str, retrieved_docs: List) -> Dict:
        """Calculate basic evaluation metrics"""
        # Simple word overlap metric
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            word_overlap = 0
        else:
            word_overlap = len(expected_words.intersection(actual_words)) / len(expected_words)
        
        # Check if answer is non-empty
        has_answer = len(actual.strip()) > 0
        
        # Check retrieval
        num_docs_retrieved = len(retrieved_docs)
        avg_relevance = sum([doc.get('relevance_percentage', 0) for doc in retrieved_docs]) / max(num_docs_retrieved, 1)
        
        return {
            "word_overlap_score": round(word_overlap, 3),
            "has_answer": has_answer,
            "num_docs_retrieved": num_docs_retrieved,
            "avg_relevance_percentage": round(avg_relevance, 2)
        }
    
    def run_evaluation(self):
        """Run full evaluation"""
        print("Loading Q&A pairs...")
        qa_pairs = self.load_qa_pairs()
        print(f"Loaded {len(qa_pairs)} Q&A pairs\n")
        
        print("Starting evaluation...\n")
        start_time = time.time()
        
        for idx, qa in enumerate(qa_pairs, 1):
            print(f"[{idx}/{len(qa_pairs)}] Processing: {qa['question'][:60]}...")
            
            # Query RAG system
            response = self.query_rag(qa['question'])
            
            # Calculate metrics
            metrics = self.calculate_metrics(
                qa['answer'],
                response.get('answer', ''),
                response.get('source_documents', [])
            )
            
            # Store result
            result = {
                "question_id": idx,
                "question": qa['question'],
                "expected_answer": qa['answer'],
                "actual_answer": response.get('answer', ''),
                "document": qa['document'],
                "error": response.get('error'),
                **metrics,
                "trace": response.get('trace', {}),
                "source_documents": response.get('source_documents', [])
            }
            
            self.results.append(result)
            print(f"  Word Overlap: {metrics['word_overlap_score']:.2%}, Relevance: {metrics['avg_relevance_percentage']:.1f}%")
        
        total_time = time.time() - start_time
        print(f"\nEvaluation completed in {total_time:.2f} seconds")
        
        return self.results
    
    def generate_report(self):
        """Generate evaluation report"""
        if not self.results:
            print("No results to report")
            return
        
        # Calculate summary statistics
        total_questions = len(self.results)
        successful_queries = sum(1 for r in self.results if not r.get('error'))
        avg_word_overlap = sum(r['word_overlap_score'] for r in self.results) / total_questions
        avg_relevance = sum(r['avg_relevance_percentage'] for r in self.results) / total_questions
        
        # Calculate timing stats
        total_time = sum(r['trace'].get('total_time_ms', 0) for r in self.results)
        avg_time = total_time / total_questions
        
        # Calculate cost stats
        total_cost = sum(r['trace'].get('cost_total_usd', 0) for r in self.results)
        
        print("\n" + "="*60)
        print("RAG EVALUATION REPORT")
        print("="*60)
        print(f"\nOverall Metrics:")
        print(f"  Total Questions: {total_questions}")
        print(f"  Successful Queries: {successful_queries} ({successful_queries/total_questions:.1%})")
        print(f"  Avg Word Overlap Score: {avg_word_overlap:.1%}")
        print(f"  Avg Retrieval Relevance: {avg_relevance:.1f}%")
        print(f"  Avg Response Time: {avg_time:.0f}ms")
        print(f"  Total Cost: ${total_cost:.4f}")
        print(f"  Avg Cost per Query: ${total_cost/total_questions:.4f}")
        
        # Per-document breakdown
        print(f"\nPer-Document Breakdown:")
        doc_stats = {}
        for r in self.results:
            doc = r['document']
            if doc not in doc_stats:
                doc_stats[doc] = []
            doc_stats[doc].append(r)
        
        for doc, results in doc_stats.items():
            avg_overlap = sum(r['word_overlap_score'] for r in results) / len(results)
            avg_rel = sum(r['avg_relevance_percentage'] for r in results) / len(results)
            print(f"\n  {doc}:")
            print(f"    Questions: {len(results)}")
            print(f"    Avg Word Overlap: {avg_overlap:.1%}")
            print(f"    Avg Relevance: {avg_rel:.1f}%")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"rag_eval_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Save CSV summary
        csv_file = f"rag_eval_summary_{timestamp}.csv"
        df = pd.DataFrame([{
            "question_id": r["question_id"],
            "question": r["question"][:50] + "...",
            "document": r["document"].split("/")[-1][:30],
            "word_overlap": r["word_overlap_score"],
            "avg_relevance": r["avg_relevance_percentage"],
            "response_time_ms": r["trace"].get("total_time_ms", 0),
            "cost_usd": r["trace"].get("cost_total_usd", 0),
            "has_error": bool(r.get("error"))
        } for r in self.results])
        df.to_csv(csv_file, index=False)
        print(f"Summary CSV saved to: {csv_file}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    # Configuration
    API_URL = "http://localhost:8080"
    QA_FILE = "rag_evaluation_qa.json"
    
    # Run evaluation
    evaluator = RAGEvaluator(API_URL, QA_FILE)
    evaluator.run_evaluation()
    evaluator.generate_report()
