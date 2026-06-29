from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
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
import os
import time
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

app = FastAPI(title="RAG Bot API", description="RAG bot for PDF question answering")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    source_documents: list = []
    trace: dict = {}

vectorstore = None
rag_chain = None
embeddings = None
bm25 = None
documents = None

@app.on_event("startup")
async def startup_event():
    global vectorstore, rag_chain, embeddings, bm25, documents
    
    pdf_files = [
        "ProteinEfficiencyRatio-FinalGuidance-May2026.pdf",
        "56628397dftrv1 - Drug and Device Manufacturer Communications With Payors Q&A.pdf",
        "Guidance-Human-Factors-Marketing.pdf",
        "Master Protocols Rev Draft Guidance for Industry.pdf"
    ]
    
    all_documents = []
    for pdf_path in pdf_files:
        if not os.path.exists(pdf_path):
            print(f"Warning: PDF file not found: {pdf_path}")
            continue
        print(f"Loading {pdf_path}...")
        loader = PyPDFLoader(pdf_path)
        all_documents.extend(loader.load())
    
    if not all_documents:
        raise Exception("No PDF files found to load")
    
    print(f"Loaded {len(all_documents)} pages from {len(pdf_files)} documents")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    splits = text_splitter.split_documents(all_documents)
    
    # Store documents globally for BM25
    documents = splits
    
    # Initialize BM25 for keyword search
    tokenized_corpus = [doc.page_content.lower().split() for doc in splits]
    bm25 = BM25Okapi(tokenized_corpus)
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_db",
        collection_metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    
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
    
    print("RAG system initialized successfully!")

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/query", response_model=QueryResponse)
async def query_pdf(request: QueryRequest):
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        start_time = time.time()
        trace = {}
        
        # 1. Semantic Search
        semantic_start = time.time()
        semantic_docs = vectorstore.max_marginal_relevance_search(
            request.question,
            k=5,
            fetch_k=10,
            lambda_mult=0.5
        )
        trace['semantic_search_ms'] = round((time.time() - semantic_start) * 1000, 2)
        
        # 2. Keyword Search
        keyword_start = time.time()
        tokenized_query = request.question.lower().split()
        bm25_scores = bm25.get_scores(tokenized_query)
        top_bm25_indices = np.argsort(bm25_scores)[-5:][::-1]
        keyword_docs = [documents[i] for i in top_bm25_indices]
        trace['keyword_search_ms'] = round((time.time() - keyword_start) * 1000, 2)
        
        # 3. Hybrid scoring
        scoring_start = time.time()
        query_embedding = embeddings.embed_query(request.question)
        
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
                    'keyword_score': 0.0,
                    'method': 'semantic'
                }
        
        for idx, doc in zip(top_bm25_indices, keyword_docs):
            doc_key = doc.page_content[:100]
            keyword_score = bm25_scores[idx]
            
            if doc_key in hybrid_results:
                hybrid_results[doc_key]['keyword_score'] = keyword_score
                hybrid_results[doc_key]['method'] = 'hybrid'
            else:
                doc_embedding = embeddings.embed_query(doc.page_content)
                semantic_score = np.dot(doc_embedding, query_embedding) / (
                    np.linalg.norm(doc_embedding) * np.linalg.norm(query_embedding)
                )
                hybrid_results[doc_key] = {
                    'doc': doc,
                    'semantic_score': semantic_score,
                    'keyword_score': keyword_score,
                    'method': 'keyword'
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
        
        trace['hybrid_scoring_ms'] = round((time.time() - scoring_start) * 1000, 2)
        
        # 4. LLM Generation
        llm_start = time.time()
        
        # Estimate input tokens
        context_text = "\n\n".join([r['doc'].page_content for r in sorted_results])
        prompt_text = f"{context_text}\n\nQuestion: {request.question}"
        input_tokens = len(prompt_text) // 4  # Rough estimate: 1 token ≈ 4 chars
        
        answer = rag_chain.invoke(request.question)
        
        llm_time = time.time() - llm_start
        trace['llm_generation_ms'] = round(llm_time * 1000, 2)
        
        # Estimate output tokens
        output_tokens = len(answer) // 4
        
        # Calculate cost (Claude Sonnet 4.5 pricing)
        # Input: $3 per 1M tokens, Output: $15 per 1M tokens
        input_cost = (input_tokens / 1_000_000) * 3.0
        output_cost = (output_tokens / 1_000_000) * 15.0
        total_cost = input_cost + output_cost
        
        trace['tokens_input'] = input_tokens
        trace['tokens_output'] = output_tokens
        trace['tokens_total'] = input_tokens + output_tokens
        trace['cost_input_usd'] = round(input_cost, 6)
        trace['cost_output_usd'] = round(output_cost, 6)
        trace['cost_total_usd'] = round(total_cost, 6)
        
        # Total time
        total_time = time.time() - start_time
        trace['total_time_ms'] = round(total_time * 1000, 2)
        trace['total_time_s'] = round(total_time, 2)
        
        sources = []
        for idx, result in enumerate(sorted_results, 1):
            doc = result['doc']
            page_num = doc.metadata.get('page', 'Unknown')
            source_file = doc.metadata.get('source', 'ProteinEfficiencyRatio-FinalGuidance-May2026.pdf')
            
            sources.append({
                "rank": idx,
                "content": doc.page_content[:250],  # Longer excerpt for citations
                "metadata": doc.metadata,
                "similarity_score": round(float(1 - result['semantic_score']), 4),
                "relevance_percentage": round(result['hybrid_score'] * 100, 2),
                "search_method": result['method'],
                "keyword_score": round(float(result['keyword_score']), 2),
                "semantic_score": round(float(result['semantic_score'] * 100), 2),
                "citation": f"[{idx}] {source_file}, Page {page_num + 1 if isinstance(page_num, int) else page_num}"
            })
        
        return QueryResponse(
            answer=answer,
            source_documents=sources,
            trace=trace
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "rag_initialized": rag_chain is not None
    }
