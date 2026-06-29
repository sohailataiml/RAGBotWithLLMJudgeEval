import json
import requests
import time
from datetime import datetime
from typing import List, Dict
import pandas as pd
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

class RAGEvaluatorWithJudge:
    def __init__(self, api_url: str, qa_file: str):
        self.api_url = api_url
        self.qa_file = qa_file
        self.results = []
        self.judge_llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
    
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
    
    def judge_answer(self, question: str, expected: str, actual: str, retrieved_docs: List) -> Dict:
        """Use LLM as a judge to evaluate the answer"""
        
        # Extract source content
        sources_text = "\n\n".join([
            f"Source {i+1} (Relevance: {doc.get('relevance_percentage', 0)}%):\n{doc.get('content', '')}"
            for i, doc in enumerate(retrieved_docs[:3])
        ])
        
        judge_prompt = f"""You are an expert evaluator assessing RAG (Retrieval-Augmented Generation) system outputs.

Question: {question}

Expected Answer (Ground Truth):
{expected}

Actual Answer (RAG System Output):
{actual}

Retrieved Context:
{sources_text}

Evaluate the RAG system output on the following criteria (score 1-5 for each):

1. **Correctness**: Does the actual answer match the ground truth in terms of factual accuracy?
   - 5: Completely correct, all key facts present
   - 4: Mostly correct, minor omissions
   - 3: Partially correct, some errors or missing info
   - 2: Largely incorrect, major errors
   - 1: Completely wrong or irrelevant

2. **Completeness**: Does the actual answer cover all important points from the ground truth?
   - 5: All key points covered comprehensively
   - 4: Most key points covered
   - 3: Some key points covered
   - 2: Few key points covered
   - 1: Almost no key points covered

3. **Relevance**: Is the actual answer relevant to the question asked?
   - 5: Highly relevant, directly answers question
   - 4: Mostly relevant
   - 3: Somewhat relevant
   - 2: Barely relevant
   - 1: Not relevant

4. **Retrieval Quality**: Did the system retrieve relevant context to answer the question?
   - 5: Perfect retrieval, all necessary info present
   - 4: Good retrieval, most necessary info present
   - 3: Adequate retrieval, some necessary info present
   - 2: Poor retrieval, little relevant info
   - 1: Failed retrieval, no relevant info

5. **Hallucination Check**: Does the answer contain information not supported by the retrieved context?
   - 5: No hallucination, fully grounded
   - 4: Minimal hallucination, mostly grounded
   - 3: Some hallucination present
   - 2: Significant hallucination
   - 1: Mostly hallucinated content

Respond ONLY with valid JSON in this exact format:
{{
  "correctness": <score>,
  "completeness": <score>,
  "relevance": <score>,
  "retrieval_quality": <score>,
  "hallucination_check": <score>,
  "overall_score": <average of all scores>,
  "reasoning": "<brief 1-2 sentence explanation>"
}}"""
        
        try:
            response = self.judge_llm.invoke(judge_prompt)
            content = response.content
            
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            scores = json.loads(content)
            return scores
        except Exception as e:
            print(f"  Judge evaluation failed: {e}")
            return {
                "correctness": 0,
                "completeness": 0,
                "relevance": 0,
                "retrieval_quality": 0,
                "hallucination_check": 0,
                "overall_score": 0,
                "reasoning": f"Evaluation error: {str(e)}"
            }
    
    def calculate_basic_metrics(self, expected: str, actual: str, retrieved_docs: List) -> Dict:
        """Calculate basic evaluation metrics"""
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            word_overlap = 0
        else:
            word_overlap = len(expected_words.intersection(actual_words)) / len(expected_words)
        
        has_answer = len(actual.strip()) > 0
        num_docs_retrieved = len(retrieved_docs)
        avg_relevance = sum([doc.get('relevance_percentage', 0) for doc in retrieved_docs]) / max(num_docs_retrieved, 1)
        
        return {
            "word_overlap_score": round(word_overlap, 3),
            "has_answer": has_answer,
            "num_docs_retrieved": num_docs_retrieved,
            "avg_relevance_percentage": round(avg_relevance, 2)
        }
    
    def run_evaluation(self):
        """Run full evaluation with LLM judge"""
        print("Loading Q&A pairs...")
        qa_pairs = self.load_qa_pairs()
        print(f"Loaded {len(qa_pairs)} Q&A pairs\n")
        
        print("Starting evaluation with LLM Judge...\n")
        start_time = time.time()
        
        for idx, qa in enumerate(qa_pairs, 1):
            print(f"[{idx}/{len(qa_pairs)}] Processing: {qa['question'][:60]}...")
            
            # Query RAG system
            response = self.query_rag(qa['question'])
            
            # Calculate basic metrics
            basic_metrics = self.calculate_basic_metrics(
                qa['answer'],
                response.get('answer', ''),
                response.get('source_documents', [])
            )
            
            # Judge evaluation
            if response.get('answer'):
                print(f"  Running LLM judge evaluation...")
                judge_scores = self.judge_answer(
                    qa['question'],
                    qa['answer'],
                    response.get('answer', ''),
                    response.get('source_documents', [])
                )
            else:
                judge_scores = {
                    "correctness": 0,
                    "completeness": 0,
                    "relevance": 0,
                    "retrieval_quality": 0,
                    "hallucination_check": 0,
                    "overall_score": 0,
                    "reasoning": "No answer generated"
                }
            
            # Store result
            result = {
                "question_id": idx,
                "question": qa['question'],
                "expected_answer": qa['answer'],
                "actual_answer": response.get('answer', ''),
                "document": qa['document'],
                "error": response.get('error'),
                **basic_metrics,
                **judge_scores,
                "trace": response.get('trace', {}),
                "source_documents": response.get('source_documents', [])
            }
            
            self.results.append(result)
            print(f"  Judge Overall Score: {judge_scores.get('overall_score', 0):.1f}/5.0")
            print(f"  Word Overlap: {basic_metrics['word_overlap_score']:.2%}, Relevance: {basic_metrics['avg_relevance_percentage']:.1f}%")
        
        total_time = time.time() - start_time
        print(f"\nEvaluation completed in {total_time:.2f} seconds")
        
        return self.results
    
    def generate_report(self):
        """Generate evaluation report with judge scores"""
        if not self.results:
            print("No results to report")
            return
        
        total_questions = len(self.results)
        successful_queries = sum(1 for r in self.results if not r.get('error'))
        
        # Basic metrics
        avg_word_overlap = sum(r['word_overlap_score'] for r in self.results) / total_questions
        avg_relevance = sum(r['avg_relevance_percentage'] for r in self.results) / total_questions
        
        # Judge scores
        avg_correctness = sum(r.get('correctness', 0) for r in self.results) / total_questions
        avg_completeness = sum(r.get('completeness', 0) for r in self.results) / total_questions
        avg_relevance_judge = sum(r.get('relevance', 0) for r in self.results) / total_questions
        avg_retrieval = sum(r.get('retrieval_quality', 0) for r in self.results) / total_questions
        avg_hallucination = sum(r.get('hallucination_check', 0) for r in self.results) / total_questions
        avg_overall = sum(r.get('overall_score', 0) for r in self.results) / total_questions
        
        # Timing and cost
        total_time = sum(r['trace'].get('total_time_ms', 0) for r in self.results)
        avg_time = total_time / total_questions
        total_cost = sum(r['trace'].get('cost_total_usd', 0) for r in self.results)
        
        print("\n" + "="*70)
        print("RAG EVALUATION REPORT (WITH LLM JUDGE)")
        print("="*70)
        
        print(f"\nOverall Metrics:")
        print(f"  Total Questions: {total_questions}")
        print(f"  Successful Queries: {successful_queries} ({successful_queries/total_questions:.1%})")
        
        print(f"\nLLM Judge Scores (out of 5):")
        print(f"  Overall Score: {avg_overall:.2f}")
        print(f"  Correctness: {avg_correctness:.2f}")
        print(f"  Completeness: {avg_completeness:.2f}")
        print(f"  Relevance: {avg_relevance_judge:.2f}")
        print(f"  Retrieval Quality: {avg_retrieval:.2f}")
        print(f"  Hallucination Check: {avg_hallucination:.2f}")
        
        print(f"\nBasic Metrics:")
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
            avg_score = sum(r.get('overall_score', 0) for r in results) / len(results)
            avg_correct = sum(r.get('correctness', 0) for r in results) / len(results)
            print(f"\n  {doc}:")
            print(f"    Questions: {len(results)}")
            print(f"    Avg Overall Score: {avg_score:.2f}/5.0")
            print(f"    Avg Correctness: {avg_correct:.2f}/5.0")
        
        # Top and bottom performers
        print(f"\nTop 3 Best Answers (by Judge Score):")
        sorted_results = sorted(self.results, key=lambda x: x.get('overall_score', 0), reverse=True)
        for i, r in enumerate(sorted_results[:3], 1):
            print(f"  {i}. Q{r['question_id']}: {r['question'][:50]}... (Score: {r.get('overall_score', 0):.1f}/5.0)")
        
        print(f"\nTop 3 Weakest Answers (by Judge Score):")
        for i, r in enumerate(sorted_results[-3:], 1):
            print(f"  {i}. Q{r['question_id']}: {r['question'][:50]}... (Score: {r.get('overall_score', 0):.1f}/5.0)")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"rag_eval_judge_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Save CSV summary
        csv_file = f"rag_eval_judge_summary_{timestamp}.csv"
        df = pd.DataFrame([{
            "question_id": r["question_id"],
            "question": r["question"][:50] + "...",
            "document": r["document"].split("/")[-1][:30],
            "judge_overall": r.get("overall_score", 0),
            "judge_correctness": r.get("correctness", 0),
            "judge_completeness": r.get("completeness", 0),
            "judge_relevance": r.get("relevance", 0),
            "judge_retrieval": r.get("retrieval_quality", 0),
            "judge_hallucination": r.get("hallucination_check", 0),
            "word_overlap": r["word_overlap_score"],
            "avg_relevance": r["avg_relevance_percentage"],
            "response_time_ms": r["trace"].get("total_time_ms", 0),
            "cost_usd": r["trace"].get("cost_total_usd", 0),
            "has_error": bool(r.get("error"))
        } for r in self.results])
        df.to_csv(csv_file, index=False)
        print(f"Summary CSV saved to: {csv_file}")
        
        print("\n" + "="*70)

if __name__ == "__main__":
    # Configuration
    API_URL = "http://localhost:8080"
    QA_FILE = "rag_evaluation_qa.json"
    
    # Run evaluation with LLM judge
    evaluator = RAGEvaluatorWithJudge(API_URL, QA_FILE)
    evaluator.run_evaluation()
    evaluator.generate_report()
