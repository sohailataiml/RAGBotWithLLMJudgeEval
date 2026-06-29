# RAG Chat Bot & Evaluation Dashboard

A production-ready Retrieval Augmented Generation (RAG) system with comprehensive evaluation framework. The project consists of two applications:

1. **RAG Chat Bot** (Port 8080) - Multi-document Q&A system with hybrid search
2. **Evaluation Dashboard** (Port 5173) - LLM-as-Judge evaluation metrics and visualization

![Architecture](https://img.shields.io/badge/Architecture-RAG-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![License](https://img.shields.io/badge/License-FDA-yellow)

---

## 🎯 Features

### RAG Chat Bot
- ✅ **Multi-Document Support**: Query across multiple FDA guidance documents
- ✅ **Hybrid Search**: Combines semantic (60%) and keyword (40%) search
- ✅ **Source Citations**: Ranked sources with page numbers and relevance scores
- ✅ **Performance Tracing**: Real-time latency, token usage, and cost tracking
- ✅ **Cost Efficient**: Local embeddings (no API costs for vectorization)

### Evaluation Dashboard
- 📊 **LLM-as-Judge Evaluation**: Automated quality assessment with Claude
- 📈 **Interactive Visualizations**: Charts for metrics, scores, and performance
- 🎯 **Comprehensive Metrics**: Correctness, Completeness, Relevance, Retrieval Quality, Hallucination
- 📋 **Document-wise Analysis**: Performance breakdown by source document
- 💡 **Insights**: Automatic strengths and weaknesses identification

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG SYSTEM ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐      ┌─────────────────────┐    │
│  │   RAG Chat Bot       │      │  Evaluation System  │    │
│  │   (Port 8080)        │      │  (Port 5173)        │    │
│  ├──────────────────────┤      ├─────────────────────┤    │
│  │ • Multi-PDF Q&A      │      │ • Q&A Generation    │    │
│  │ • Hybrid Search      │      │ • LLM Judge         │    │
│  │ • Claude Sonnet 4.5  │      │ • React Dashboard   │    │
│  │ • ChromaDB           │      │ • Metrics & Charts  │    │
│  │ • FastAPI Server     │      │ • Result Analysis   │    │
│  └──────────────────────┘      └─────────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Document Collection                     │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ • Protein Efficiency Ratio Guidance (47 pages)       │  │
│  │ • Drug/Device Manufacturer Communications (15 pages) │  │
│  │ • Human Factors Marketing Guidance (42 pages)        │  │
│  │ • Master Protocols Guidance (47 pages)               │  │
│  │ Total: 151 pages indexed                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### RAG Chat Bot (Port 8080)
- **Framework**: FastAPI (REST API)
- **LLM**: Claude Sonnet 4.5 (Anthropic)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector DB**: ChromaDB with cosine similarity
- **Keyword Search**: BM25Okapi
- **PDF Processing**: PyPDF

#### Evaluation Dashboard (Port 5173)
- **Frontend**: React (via CDN) + Chart.js
- **Backend**: FastAPI
- **Judge LLM**: Claude Sonnet 4.5
- **Data Processing**: Pandas
- **Evaluation**: LLM-as-Judge framework

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))
- 2GB RAM minimum
- 1GB disk space

### Installation

1. **Clone the repository**
   ```bash
   git clone https://git.fda.gov/sohail.siddiqui/rag-chat-bot-and-eval-dashboard.git
   cd rag-chat-bot-and-eval-dashboard
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Add your Anthropic API key
   ```
   
   Add:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your_key_here
   ```

---

## 🎮 Running the Applications

### Option 1: Run RAG Chat Bot (Port 8080)

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080
```

Access at: **http://localhost:8080**

### Option 2: Run Evaluation Dashboard (Port 5173)

```bash
source venv/bin/activate
uvicorn dashboard_server:app --host 0.0.0.0 --port 5173
```

Access at: **http://localhost:5173**

### Option 3: Run Both Applications

**Terminal 1 - RAG Bot:**
```bash
cd /path/to/project
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080
```

**Terminal 2 - Dashboard:**
```bash
cd /path/to/project
source venv/bin/activate
uvicorn dashboard_server:app --host 0.0.0.0 --port 5173
```

---

## 📖 Usage

### Using the RAG Chat Bot

1. Open **http://localhost:8080** in your browser
2. Wait for initialization (~10-20 seconds first run)
3. Ask questions about any of the loaded FDA guidance documents
4. View AI-generated answers with:
   - Ranked source citations
   - Search method indicators
   - Performance metrics
   - Token usage and cost

**Example Questions:**
- "What is protein efficiency ratio?"
- "What are the FDA requirements for human factors testing?"
- "How do master protocols work?"
- "What are the communication guidelines for manufacturers?"

### Using the Evaluation Dashboard

1. Open **http://localhost:5173** in your browser
2. View comprehensive evaluation metrics:
   - Overall judge scores (Correctness, Completeness, Relevance)
   - Document-wise performance breakdown
   - Score distribution charts
   - Detailed results table with per-question metrics
   - Strengths and weaknesses analysis

---

## 🧪 Running Evaluations

### Step 1: Generate Q&A Pairs

```bash
source venv/bin/activate
python generate_qa.py
```

Output: `rag_evaluation_qa.json` (20 Q&A pairs)

### Step 2: Run Basic Evaluation

```bash
python rag_evaluation.py
```

Generates:
- `rag_eval_results_[timestamp].json`
- `rag_eval_summary_[timestamp].csv`

### Step 3: Run LLM-as-Judge Evaluation

```bash
python rag_evaluation_judge.py
```

Generates:
- `rag_eval_judge_results_[timestamp].json`
- `rag_eval_judge_summary_[timestamp].csv`

### Step 4: View Results in Dashboard

Start the dashboard and view the latest evaluation results automatically.

---

## 📊 Evaluation Metrics

### LLM Judge Scores (1-5 scale)

| Metric | Description | Current Avg |
|--------|-------------|-------------|
| **Correctness** | Factual accuracy vs ground truth | 2.70/5 |
| **Completeness** | Coverage of key points | 2.45/5 |
| **Relevance** | Answer addresses the question | 4.10/5 |
| **Retrieval Quality** | Retrieved context quality | 1.85/5 |
| **Hallucination Check** | Answer grounded in sources | 4.15/5 |
| **Overall Score** | Average of all metrics | 2.76/5 |

### Performance Metrics

- Success Rate: 100%
- Avg Response Time: 4.2 seconds
- Avg Cost per Query: $0.0044
- Total Queries Evaluated: 20

---

## 📁 Project Structure

```
rag-chat-bot-and-eval-dashboard/
├── main.py                              # RAG chat bot FastAPI server
├── dashboard_server.py                  # Evaluation dashboard server
├── dashboard.html                       # React dashboard frontend
├── index.html                          # RAG bot UI
├── generate_qa.py                      # Q&A generation script
├── rag_evaluation.py                   # Basic evaluation metrics
├── rag_evaluation_judge.py             # LLM-as-judge evaluation
├── run_server.py                       # Simplified server startup
├── start.sh                            # Legacy startup script
├── requirements.txt                    # Python dependencies
├── .env                               # Environment variables (API keys)
├── .env.example                       # Template for .env
├── README.md                          # This file
├── SYSTEM_PROMPT.md                   # AI behavior documentation
├── RAG_Bot_Architecture.pptx          # Architecture presentation
├── rag_evaluation_qa.json             # Generated Q&A pairs
├── rag_eval_judge_results_*.json      # Latest judge results
├── rag_eval_judge_summary_*.csv       # Latest judge summary
├── Documents/
│   ├── ProteinEfficiencyRatio-FinalGuidance-May2026.pdf
│   ├── 56628397dftrv1 - Drug and Device Manufacturer Communications With Payors Q&A.pdf
│   ├── Guidance-Human-Factors-Marketing.pdf
│   └── Master Protocols Rev Draft Guidance for Industry.pdf
├── chroma_db/                         # Vector database storage
└── venv/                              # Python virtual environment
```

---

## 🔍 API Documentation

### RAG Chat Bot APIs (Port 8080)

**Query Endpoint:**
```bash
POST http://localhost:8080/query
Content-Type: application/json

{
  "question": "What is protein efficiency ratio?"
}
```

**Health Check:**
```bash
GET http://localhost:8080/health
```

### Evaluation Dashboard APIs (Port 5173)

**Get Evaluation Data:**
```bash
GET http://localhost:5173/api/evaluation-data
```

**Health Check:**
```bash
GET http://localhost:5173/health
```

Interactive API docs:
- RAG Bot: http://localhost:8080/docs
- Dashboard: http://localhost:5173/docs

---

## 🔧 Configuration

### Adjusting Search Weights

Edit `main.py` line 197:
```python
result['hybrid_score'] = (0.6 * result['semantic_score']) + (0.4 * norm_keyword)
# Change to (0.7 * semantic) + (0.3 * keyword) for more semantic bias
```

### Adding New Documents

1. Place PDF in project root
2. Edit `main.py` lines 52-57:
```python
pdf_files = [
    "ProteinEfficiencyRatio-FinalGuidance-May2026.pdf",
    "YourNewDocument.pdf",  # Add here
    # ... other files
]
```

### Changing LLM Model

Edit `main.py` line 86:
```python
llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
# Options: claude-3-5-sonnet-20241022, claude-3-opus-20240229, etc.
```

---

## 🧪 Testing

### Test RAG Bot
```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is protein efficiency ratio?"}'
```

### Test Dashboard
```bash
curl http://localhost:5173/api/evaluation-data
```

---

## 🚢 Deployment

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080 5173

CMD ["bash", "-c", "uvicorn main:app --host 0.0.0.0 --port 8080 & uvicorn dashboard_server:app --host 0.0.0.0 --port 5173"]
```

**Build and run:**
```bash
docker build -t rag-system .
docker run -p 8080:8080 -p 5173:5173 --env-file .env rag-system
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Merge Request

---

## 📝 License

This project is developed for FDA internal use. All rights reserved.

---

## 👥 Authors

**Sohail Siddiqui**
- FDA Email: sohail.siddiqui@fda.hhs.gov
- Git: https://git.fda.gov/sohail.siddiqui

---

## 🙏 Acknowledgments

- **LangChain** - RAG framework
- **Anthropic** - Claude LLM
- **HuggingFace** - Embedding models
- **ChromaDB** - Vector database
- **FastAPI** - Web framework
- **Chart.js** - Visualization library
- **React** - Dashboard UI

---

## 📞 Support

For issues, questions, or feature requests:
1. Open an issue on GitLab: https://git.fda.gov/sohail.siddiqui/rag-chat-bot-and-eval-dashboard/issues
2. Contact via FDA email: sohail.siddiqui@fda.hhs.gov

---

## 🗺️ Roadmap

### Completed
- [x] Multi-document support (4 FDA guidances)
- [x] Hybrid search implementation
- [x] LLM-as-judge evaluation framework
- [x] Interactive evaluation dashboard
- [x] Automated Q&A generation

### Planned Features
- [ ] Chat history persistence
- [ ] User authentication
- [ ] Response streaming
- [ ] PDF highlighting
- [ ] Export conversations
- [ ] Comparative evaluation (multiple RAG configs)
- [ ] A/B testing framework
- [ ] Real-time monitoring dashboard

---

**Last Updated:** June 2026  
**Version:** 2.0.0
