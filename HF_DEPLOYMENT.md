# Hugging Face Deployment Guide

## 🚀 Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
cd /rag-chat-bot
./deploy_to_hf.sh
```

The script will:
1. Ask for your Hugging Face token
2. Ask for your username
3. Create and push a Hugging Face Space
4. Provide the URL to your deployed app

### Option 2: Manual Deployment

1. **Create a Hugging Face Space:**
   - Go to https://huggingface.co/new-space
   - Name: `RAGBotWithLLMJudgeEval`
   - SDK: Gradio
   - Python: 3.11

2. **Clone and push:**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/RAGBotWithLLMJudgeEval
   cd RAGBotWithLLMJudgeEval
   
   # Copy files from this repo
   cp /path/to/rag-chat-bot/app.py .
   cp /path/to/rag-chat-bot/requirements_hf.txt requirements.txt
   cp /path/to/rag-chat-bot/README_HF.md README.md
   cp /path/to/rag-chat-bot/*.pdf .
   
   git add .
   git commit -m "Deploy RAG Chat Bot"
   git push
   ```

3. **Set API Key:**
   - Go to Space Settings → Secrets
   - Add: `ANTHROPIC_API_KEY` = `your_key_here`

4. **Wait for build** (~5-10 minutes)

## 📋 What Gets Deployed

### Files Included:
- ✅ `app.py` - Gradio interface
- ✅ `requirements.txt` - Dependencies
- ✅ `README.md` - Space description
- ✅ All 4 PDF documents
- ✅ Evaluation data (optional)

### Features:
- 💬 Chat interface with RAG
- 📊 Evaluation metrics viewer
- 📚 4 FDA guidance documents
- 🔍 Hybrid search (semantic + keyword)
- 📈 Source citations with relevance scores

## ⚙️ Configuration

### Required Secrets:
- `ANTHROPIC_API_KEY` - Your Anthropic API key

### Optional Settings:
- Hardware: CPU Basic (free) is sufficient
- Visibility: Public or Private
- SDK: Gradio 4.44.0
- Python: 3.11

## 🧪 Testing Locally

Before deployment, test locally:

```bash
cd /rag-chat-bot
pip install -r requirements_hf.txt
export ANTHROPIC_API_KEY=your_key_here
python app.py
```

Open: http://localhost:7860

## 🐛 Troubleshooting

### Issue: "ANTHROPIC_API_KEY not found"
**Solution:** Set the secret in Space Settings → Secrets

### Issue: "PDF files not found"
**Solution:** Ensure PDFs are in the root directory when deploying

### Issue: "Out of memory"
**Solution:** 
- Use CPU Basic (should work)
- If needed, upgrade to CPU Upgrade ($5/month)

### Issue: "Build timeout"
**Solution:** 
- Wait longer (first build takes ~10 min)
- Check build logs in Space

## 📊 Performance on HF Spaces

- **First load:** ~30-60 seconds (loads embeddings)
- **Subsequent queries:** ~3-5 seconds
- **Memory usage:** ~2-3GB
- **CPU:** Sufficient for embedding + inference

## 🔗 Links

- **HF Spaces Docs:** https://huggingface.co/docs/hub/spaces
- **Gradio Docs:** https://gradio.app/docs/
- **GitHub Repo:** https://github.com/sohailataiml/RAGBotWithLLMJudgeEval

## 💡 Tips

1. **First deployment:** Use automated script for easier setup
2. **API costs:** Monitor your Anthropic usage
3. **Updates:** Push new commits to update the Space
4. **Custom domain:** Available with HF Pro subscription

## 📞 Support

Issues? Open a ticket:
- GitHub: https://github.com/sohailataiml/RAGBotWithLLMJudgeEval/issues
- HF Community: https://huggingface.co/spaces/community
