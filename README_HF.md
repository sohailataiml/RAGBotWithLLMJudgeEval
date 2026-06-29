---
title: RAG Chat Bot with LLM Judge Eval
emoji: 🎯
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
python_version: 3.11
---

# RAG Chat Bot with LLM-as-Judge Evaluation

A production-ready Retrieval Augmented Generation (RAG) system with comprehensive LLM-as-Judge evaluation framework.

## 🎯 Features

- **Multi-Document RAG**: Query across 4 FDA guidance documents
- **Hybrid Search**: 60% Semantic + 40% Keyword search
- **Source Citations**: Ranked sources with relevance scores
- **LLM-as-Judge**: Automated quality evaluation
- **Interactive UI**: Built with Gradio

## 🚀 Quick Start

1. **Set API Key**: Add `ANTHROPIC_API_KEY` in Space settings → Secrets
2. **Wait for initialization** (~30 seconds first run)
3. **Ask questions** about FDA guidance documents

## 📚 Documents Included

1. Protein Efficiency Ratio Guidance (47 pages)
2. Drug and Device Manufacturer Communications (15 pages)  
3. Human Factors Marketing Guidance (42 pages)
4. Master Protocols Guidance (47 pages)

## 🏗️ Architecture

- **LLM:** Claude Sonnet 4.5 (Anthropic)
- **Embeddings:** sentence-transformers/all-MiniLM-L6-v2
- **Vector DB:** ChromaDB
- **Keyword Search:** BM25Okapi
- **Framework:** LangChain

## 📊 Evaluation Metrics

- Correctness: 2.70/5
- Completeness: 2.45/5
- Relevance: 4.10/5
- Retrieval Quality: 1.85/5
- Hallucination Check: 4.15/5

## 🔗 Links

- **GitHub:** [RAGBotWithLLMJudgeEval](https://github.com/sohailataiml/RAGBotWithLLMJudgeEval)
- **FDA GitLab:** [rag-chat-bot-and-eval-dashbaord](https://git.fda.gov/sohail.siddiqui/rag-chat-bot-and-eval-dashbaord)

## 👤 Author

**Sohail Siddiqui**
- Email: sohail.siddiqui@fda.hhs.gov
