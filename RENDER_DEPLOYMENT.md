# Render Deployment Guide

## 🚀 Deploy to Render (Recommended for Production)

Render is perfect for this application because:
- ✅ Supports Docker deployment
- ✅ Can run multiple services (RAG Bot + Dashboard)
- ✅ Free tier available ($0/month with limits)
- ✅ Easy environment variable management
- ✅ Automatic HTTPS
- ✅ No cold starts (unlike serverless)

---

## 📦 Deployment Options

### Option 1: Blueprint Deploy (Easiest)

1. **Push code to GitHub** (already done!)
   - Repository: https://github.com/sohailataiml/RAGBotWithLLMJudgeEval

2. **Click Deploy to Render:**
   - Go to https://render.com/deploy
   - Connect your GitHub account
   - Select repository: `sohailataiml/RAGBotWithLLMJudgeEval`
   - Render will auto-detect `render.yaml`

3. **Set Environment Variables:**
   - `ANTHROPIC_API_KEY` = your_anthropic_key

4. **Deploy!** 
   - Render will build and deploy automatically
   - Takes ~5-10 minutes

### Option 2: Manual Deploy

#### Step 1: Create Web Service

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository
4. Configure:
   - **Name:** `rag-chat-bot`
   - **Region:** Oregon (or closest to you)
   - **Branch:** `main`
   - **Runtime:** Docker
   - **Docker Command:** (leave empty, uses Dockerfile CMD)
   - **Plan:** Free or Starter ($7/month)

#### Step 2: Configure Environment

Add environment variable:
- **Key:** `ANTHROPIC_API_KEY`
- **Value:** Your Anthropic API key

#### Step 3: Advanced Settings

- **Health Check Path:** `/health`
- **Auto-Deploy:** Yes (deploys on git push)

#### Step 4: Deploy

Click **"Create Web Service"**

---

## 🔧 Service Configuration

### RAG Chat Bot (Port 8080)
- **URL:** `https://rag-chat-bot.onrender.com`
- **Health Check:** `https://rag-chat-bot.onrender.com/health`
- **API Docs:** `https://rag-chat-bot.onrender.com/docs`

### Evaluation Dashboard (Port 5173)
For the dashboard, you have two options:

**Option A: Single Service with Path Routing**
- Access dashboard at: `https://rag-chat-bot.onrender.com:5173`
- Both apps run in same container

**Option B: Separate Service (Recommended)**
1. Create another Web Service
2. Name: `rag-eval-dashboard`
3. Use same repo
4. Docker Command: `uvicorn dashboard_server:app --host 0.0.0.0 --port $PORT`
5. Access at: `https://rag-eval-dashboard.onrender.com`

---

## 💰 Pricing

### Free Tier
- ✅ Good for testing
- ⚠️ Spins down after 15 min inactivity
- ⚠️ Cold start: ~30-60 seconds
- 750 hours/month free

### Starter Plan ($7/month per service)
- ✅ Always on (no spin down)
- ✅ Faster response
- ✅ More memory (512MB → 2GB)
- ✅ Better for production

**Recommended:** Starter plan for RAG bot ($7/month)

---

## 🐳 Docker Deployment Details

The Dockerfile:
1. Uses Python 3.11 slim image
2. Installs system dependencies
3. Copies all application files
4. Copies PDF documents
5. Runs both FastAPI servers

Build time: ~5-8 minutes first deploy

---

## ⚙️ Environment Variables

### Required:
- `ANTHROPIC_API_KEY` - Your Anthropic API key

### Optional:
- `PORT` - Default: 8080 (Render sets this automatically)

---

## 🧪 Testing Before Deploy

### Local Docker Test:
```bash
cd /rag-chat-bot

# Build Docker image
docker build -t rag-bot .

# Run container
docker run -p 8080:8080 -p 5173:5173 \
  -e ANTHROPIC_API_KEY=your_key_here \
  rag-bot

# Test
curl http://localhost:8080/health
curl http://localhost:5173/health
```

### Access:
- RAG Bot: http://localhost:8080
- Dashboard: http://localhost:5173

---

## 📊 Resource Requirements

### Memory:
- Minimum: 1GB RAM
- Recommended: 2GB RAM (for embeddings)

### CPU:
- Minimum: 0.5 vCPU
- Recommended: 1 vCPU

### Disk:
- ~500MB (app + models + PDFs)

### Network:
- Downloads embedding model on first start (~80MB)
- Persistent after first run

---

## 🔍 Monitoring & Logs

### View Logs:
1. Go to Render Dashboard
2. Select your service
3. Click "Logs" tab
4. Real-time logs available

### Metrics:
- CPU usage
- Memory usage
- Response times
- Error rates

### Alerts:
- Email notifications for:
  - Deployment failures
  - Service crashes
  - Health check failures

---

## 🚨 Troubleshooting

### Issue: "Build failed"
**Check:**
- Dockerfile syntax
- All required files present
- requirements.txt correct

### Issue: "Service unhealthy"
**Solutions:**
1. Check logs for errors
2. Verify ANTHROPIC_API_KEY is set
3. Check /health endpoint manually
4. Increase startup time in health check

### Issue: "Out of memory"
**Solutions:**
1. Upgrade to Starter plan (2GB RAM)
2. Optimize chunk size in code
3. Reduce number of documents loaded

### Issue: "Slow first request"
**Explanation:** 
- Embedding model loads on first request
- Subsequent requests are fast
- Use Starter plan to avoid cold starts

---

## 🔄 Continuous Deployment

### Auto-Deploy Setup:
1. Render watches your `main` branch
2. Push to GitHub triggers automatic deploy
3. No manual intervention needed

### Deploy Command:
```bash
git add .
git commit -m "Update deployment"
git push origin main
# Render auto-deploys!
```

---

## 🌐 Custom Domain

### Free Subdomain:
- Automatic: `https://rag-chat-bot.onrender.com`

### Custom Domain (Optional):
1. Go to Service Settings → Custom Domains
2. Add your domain (e.g., `ragbot.yourdomain.com`)
3. Update DNS records as shown
4. Free SSL certificate included

---

## 📈 Performance Optimization

### Tips:
1. **Use Starter plan** - No cold starts
2. **Enable caching** - Add Redis for responses
3. **Optimize embeddings** - Cache frequent queries
4. **Monitor costs** - Track Anthropic API usage
5. **Use CDN** - For static assets

### Expected Performance:
- First request: ~2-3 seconds (model load)
- Subsequent: ~2-4 seconds
- Cold start (free tier): ~30-60 seconds

---

## 🔗 Useful Links

- **Render Dashboard:** https://dashboard.render.com/
- **Render Docs:** https://render.com/docs
- **Docker Docs:** https://docs.docker.com/
- **GitHub Repo:** https://github.com/sohailataiml/RAGBotWithLLMJudgeEval

---

## 📞 Support

**Render Support:**
- Community: https://community.render.com/
- Docs: https://render.com/docs
- Status: https://status.render.com/

**App Issues:**
- GitHub: https://github.com/sohailataiml/RAGBotWithLLMJudgeEval/issues

---

## ✅ Deployment Checklist

- [ ] GitHub repo updated with latest code
- [ ] Dockerfile tested locally
- [ ] requirements.txt complete
- [ ] PDF files included in repo
- [ ] Anthropic API key ready
- [ ] Render account created
- [ ] Service configured
- [ ] Environment variables set
- [ ] Health check endpoint working
- [ ] First deployment successful
- [ ] Both services accessible
- [ ] Logs look clean
- [ ] Performance acceptable

---

**Ready to Deploy?** 

Go to: https://dashboard.render.com/ and create a new Web Service!

Or use the Blueprint Deploy: https://render.com/deploy
