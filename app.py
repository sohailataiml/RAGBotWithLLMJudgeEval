import gradio as gr
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from rank_bm25 import BM25Okapi
import numpy as np
import time
import json
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Global variables
vectorstore = None
rag_chain = None
embeddings = None
bm25 = None
documents = None

def initialize_rag():
    """Initialize the RAG system"""
    global vectorstore, rag_chain, embeddings, bm25, documents
    
    status_messages = []
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "❌ Error: ANTHROPIC_API_KEY not found. Please set it in Hugging Face Space secrets."
    
    status_messages.append("✅ API key found")
    
    # Load PDFs
    pdf_files = [
        "ProteinEfficiencyRatio-FinalGuidance-May2026.pdf",
        "56628397dftrv1 - Drug and Device Manufacturer Communications With Payors Q&A.pdf",
        "Guidance-Human-Factors-Marketing.pdf",
        "Master Protocols Rev Draft Guidance for Industry.pdf"
    ]
    
    all_documents = []
    for pdf_path in pdf_files:
        if not os.path.exists(pdf_path):
            status_messages.append(f"⚠️ Warning: {pdf_path} not found, skipping...")
            continue
        status_messages.append(f"📄 Loading {pdf_path}...")
        loader = PyPDFLoader(pdf_path)
        all_documents.extend(loader.load())
    
    if not all_documents:
        return "❌ Error: No PDF files found"
    
    status_messages.append(f"✅ Loaded {len(all_documents)} pages from {len(pdf_files)} documents")
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    splits = text_splitter.split_documents(all_documents)
    documents = splits
    
    status_messages.append(f"✅ Split into {len(splits)} chunks")
    
    # Initialize BM25
    tokenized_corpus = [doc.page_content.lower().split() for doc in splits]
    bm25 = BM25Okapi(tokenized_corpus)
    status_messages.append("✅ BM25 initialized")
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    status_messages.append("✅ Embeddings model loaded")
    
    # Create vector store
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_metadata={"hnsw:space": "cosine"}
    )
    status_messages.append("✅ Vector database created")
    
    # Initialize LLM
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
    
    prompt_template = """You are an AI assistant with access to multiple FDA guidance documents. Use the following pieces of context retrieved from the documents to answer the question at the end.

IMPORTANT INSTRUCTIONS:
- Answer ONLY based on the provided context from the document
- If the context doesn't contain enough information, say so clearly
- Cite page numbers when relevant
- Be concise and direct
- Never make up information not present in the context

Context from the document:
{context}

Question: {question}

Answer (based solely on the above context):"""
    
    prompt = PromptTemplate(
        template=prompt_template, 
        input_variables=["context", "question"]
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    status_messages.append("✅ RAG chain initialized")
    status_messages.append("\n🎉 System ready! You can now ask questions.")
    
    return "\n".join(status_messages)

def query_rag(question):
    """Query the RAG system"""
    if rag_chain is None:
        return "❌ System not initialized. Please wait for initialization to complete.", ""
    
    if not question.strip():
        return "Please enter a question.", ""
    
    try:
        start_time = time.time()
        
        # Semantic search
        semantic_docs = vectorstore.max_marginal_relevance_search(
            question,
            k=5,
            fetch_k=10,
            lambda_mult=0.5
        )
        
        # Keyword search
        tokenized_query = question.lower().split()
        bm25_scores = bm25.get_scores(tokenized_query)
        top_bm25_indices = np.argsort(bm25_scores)[-5:][::-1]
        keyword_docs = [documents[i] for i in top_bm25_indices]
        
        # Hybrid scoring
        query_embedding = embeddings.embed_query(question)
        hybrid_results = {}
        
        for doc in semantic_docs:
            doc_key = doc.page_content[:100]
            if doc_key not in hybrid_results:
                doc_embedding = embeddings.embed_query(doc.page_content)
                semantic_score = np.dot(doc_embedding, query_embedding) / (
                    np.linalg.norm(doc_embedding) * np.linalg.norm(query_embedding)
                )
                hybrid_results[doc_key] = {
                    'doc': doc,
                    'semantic_score': semantic_score,
                    'keyword_score': 0.0
                }
        
        for idx, doc in zip(top_bm25_indices, keyword_docs):
            doc_key = doc.page_content[:100]
            keyword_score = bm25_scores[idx]
            
            if doc_key in hybrid_results:
                hybrid_results[doc_key]['keyword_score'] = keyword_score
            else:
                doc_embedding = embeddings.embed_query(doc.page_content)
                semantic_score = np.dot(doc_embedding, query_embedding) / (
                    np.linalg.norm(doc_embedding) * np.linalg.norm(query_embedding)
                )
                hybrid_results[doc_key] = {
                    'doc': doc,
                    'semantic_score': semantic_score,
                    'keyword_score': keyword_score
                }
        
        for key in hybrid_results:
            result = hybrid_results[key]
            max_keyword = max(bm25_scores) if max(bm25_scores) > 0 else 1
            norm_keyword = result['keyword_score'] / max_keyword
            result['hybrid_score'] = (0.6 * result['semantic_score']) + (0.4 * norm_keyword)
        
        sorted_results = sorted(
            hybrid_results.values(), 
            key=lambda x: x['hybrid_score'], 
            reverse=True
        )[:3]
        
        # Generate answer
        answer = rag_chain.invoke(question)
        
        total_time = time.time() - start_time
        
        # Format sources
        sources_text = "\n\n**📚 Sources:**\n\n"
        for idx, result in enumerate(sorted_results, 1):
            doc = result['doc']
            page_num = doc.metadata.get('page', 'Unknown')
            source_file = doc.metadata.get('source', 'Unknown').split('/')[-1]
            relevance = result['hybrid_score'] * 100
            
            sources_text += f"**[{idx}] {source_file}, Page {page_num + 1 if isinstance(page_num, int) else page_num}**\n"
            sources_text += f"Relevance: {relevance:.1f}%\n"
            sources_text += f"Preview: {doc.page_content[:200]}...\n\n"
        
        sources_text += f"\n⏱️ Response time: {total_time:.2f}s"
        
        return answer, sources_text
        
    except Exception as e:
        return f"❌ Error: {str(e)}", ""

def load_evaluation_data():
    """Load evaluation results"""
    try:
        # Find latest judge results
        import glob
        judge_files = glob.glob('rag_eval_judge_summary_*.csv')
        if not judge_files:
            return "No evaluation data found. Run evaluation first."
        
        latest_file = sorted(judge_files)[-1]
        df = pd.read_csv(latest_file)
        
        # Summary statistics
        summary = f"""
## 📊 Evaluation Summary

**Overall Metrics:**
- Total Questions: {len(df)}
- Success Rate: {(~df['has_error']).sum() / len(df) * 100:.1f}%
- Avg Response Time: {df['response_time_ms'].mean():.0f}ms
- Total Cost: ${df['cost_usd'].sum():.4f}

**LLM Judge Scores (out of 5):**
- Overall: {df['judge_overall'].mean():.2f}
- Correctness: {df['judge_correctness'].mean():.2f}
- Completeness: {df['judge_completeness'].mean():.2f}
- Relevance: {df['judge_relevance'].mean():.2f}
- Retrieval Quality: {df['judge_retrieval'].mean():.2f}
- Hallucination Check: {df['judge_hallucination'].mean():.2f}

**Per-Document Performance:**
"""
        for doc in df['document'].unique():
            doc_df = df[df['document'] == doc]
            doc_name = doc.split('/')[-1][:40]
            summary += f"\n- **{doc_name}**: {doc_df['judge_overall'].mean():.2f}/5.0 ({len(doc_df)} questions)"
        
        return summary
    except Exception as e:
        return f"Error loading evaluation data: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="RAG Chat Bot with LLM Judge Eval", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎯 RAG Chat Bot with LLM-as-Judge Evaluation
    
    Ask questions about FDA guidance documents using hybrid search (semantic + keyword) powered by Claude Sonnet 4.5.
    
    **Documents included:**
    - Protein Efficiency Ratio Guidance
    - Drug and Device Manufacturer Communications
    - Human Factors Marketing Guidance
    - Master Protocols Guidance
    """)
    
    with gr.Tabs():
        with gr.Tab("💬 Chat"):
            with gr.Row():
                with gr.Column(scale=2):
                    question_input = gr.Textbox(
                        label="Ask a Question",
                        placeholder="e.g., What is protein efficiency ratio?",
                        lines=3
                    )
                    submit_btn = gr.Button("🔍 Ask", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ Clear")
                    
                    gr.Examples(
                        examples=[
                            "What is protein efficiency ratio?",
                            "What are the FDA requirements for human factors testing?",
                            "How do master protocols work?",
                            "What are the communication guidelines for manufacturers?"
                        ],
                        inputs=question_input
                    )
            
            with gr.Row():
                with gr.Column(scale=1):
                    answer_output = gr.Markdown(label="Answer")
                with gr.Column(scale=1):
                    sources_output = gr.Markdown(label="Sources & Metrics")
            
            submit_btn.click(
                query_rag,
                inputs=[question_input],
                outputs=[answer_output, sources_output]
            )
            
            clear_btn.click(
                lambda: ("", "", ""),
                outputs=[question_input, answer_output, sources_output]
            )
        
        with gr.Tab("📊 Evaluation"):
            gr.Markdown("""
            ## LLM-as-Judge Evaluation Results
            
            View comprehensive evaluation metrics with automated quality assessment.
            """)
            
            eval_output = gr.Markdown()
            load_eval_btn = gr.Button("📈 Load Evaluation Results", variant="secondary")
            
            load_eval_btn.click(
                load_evaluation_data,
                outputs=[eval_output]
            )
        
        with gr.Tab("ℹ️ About"):
            gr.Markdown("""
            ## System Architecture
            
            **RAG Chat Bot:**
            - **LLM:** Claude Sonnet 4.5 (Anthropic)
            - **Embeddings:** sentence-transformers/all-MiniLM-L6-v2
            - **Vector DB:** ChromaDB with cosine similarity
            - **Keyword Search:** BM25Okapi
            - **Hybrid Search:** 60% Semantic + 40% Keyword
            
            **Evaluation Framework:**
            - **LLM-as-Judge:** Automated quality assessment
            - **Metrics:** Correctness, Completeness, Relevance, Retrieval Quality, Hallucination Check
            - **20 Q&A pairs** generated from documents
            
            **GitHub Repository:** [RAGBotWithLLMJudgeEval](https://github.com/sohailataiml/RAGBotWithLLMJudgeEval)
            
            ---
            
            **Author:** Sohail Siddiqui  
            **Version:** 2.0.0
            """)
    
    # Initialize on load
    demo.load(
        initialize_rag,
        outputs=[gr.Textbox(label="System Status", lines=15, visible=True)]
    )

if __name__ == "__main__":
    demo.launch()
