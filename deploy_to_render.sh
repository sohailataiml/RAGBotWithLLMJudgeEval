#!/bin/bash

# Render Deployment Script for RAG Chat Bot

echo "🚀 Deploying RAG Chat Bot to Render"
echo "===================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    exit 1
fi

# Check if Docker is installed for local testing
if command -v docker &> /dev/null; then
    DOCKER_AVAILABLE=true
    echo "✅ Docker found - you can test locally before deploying"
else
    DOCKER_AVAILABLE=false
    echo "⚠️  Docker not found - skipping local test option"
fi

echo ""
echo "📋 Pre-deployment checklist:"
echo "  [1] GitHub repository exists"
echo "  [2] All code committed and pushed"
echo "  [3] Anthropic API key ready"
echo "  [4] Render account created"
echo ""

read -p "Have you completed the checklist? (y/n): " READY

if [ "$READY" != "y" ]; then
    echo "❌ Please complete the checklist first"
    exit 1
fi

echo ""
echo "🔧 Checking deployment files..."

# Check if required files exist
REQUIRED_FILES=(
    "Dockerfile"
    "render.yaml"
    "requirements.txt"
    "main.py"
    "dashboard_server.py"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    else
        echo "  ✅ $file"
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing required files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

echo ""
echo "✅ All required files present"

# Test Docker build locally if Docker is available
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo ""
    read -p "Would you like to test Docker build locally? (y/n): " TEST_LOCAL
    
    if [ "$TEST_LOCAL" = "y" ]; then
        echo ""
        echo "🐳 Building Docker image locally..."
        docker build -t rag-bot-test . || {
            echo "❌ Docker build failed. Please fix errors before deploying."
            exit 1
        }
        
        echo ""
        echo "✅ Docker build successful!"
        echo ""
        read -p "Would you like to run the container locally? (y/n): " RUN_LOCAL
        
        if [ "$RUN_LOCAL" = "y" ]; then
            echo ""
            echo "Enter your Anthropic API key:"
            read -sp "API Key: " API_KEY
            echo ""
            
            echo "🚀 Starting container..."
            echo "RAG Bot will be at: http://localhost:8080"
            echo "Dashboard will be at: http://localhost:5173"
            echo "Press Ctrl+C to stop"
            echo ""
            
            docker run -p 8080:8080 -p 5173:5173 \
                -e ANTHROPIC_API_KEY=$API_KEY \
                rag-bot-test
            
            exit 0
        fi
    fi
fi

echo ""
echo "📤 Pushing to GitHub..."

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  You have uncommitted changes"
    read -p "Would you like to commit them now? (y/n): " COMMIT_NOW
    
    if [ "$COMMIT_NOW" = "y" ]; then
        git add .
        read -p "Commit message: " COMMIT_MSG
        git commit -m "$COMMIT_MSG"
    fi
fi

# Push to GitHub
git push origin main || {
    echo "❌ Failed to push to GitHub"
    exit 1
}

echo "✅ Code pushed to GitHub"

echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Go to Render Dashboard:"
echo "   https://dashboard.render.com/"
echo ""
echo "2. Click 'New +' → 'Web Service'"
echo ""
echo "3. Connect your GitHub repository:"
echo "   https://github.com/sohailataiml/RAGBotWithLLMJudgeEval"
echo ""
echo "4. Render will auto-detect render.yaml and configure everything"
echo ""
echo "5. Set environment variable:"
echo "   ANTHROPIC_API_KEY = your_key_here"
echo ""
echo "6. Click 'Create Web Service'"
echo ""
echo "7. Wait ~5-10 minutes for first deploy"
echo ""
echo "📊 Your services will be available at:"
echo "   RAG Bot: https://rag-chat-bot.onrender.com"
echo "   Dashboard: https://rag-eval-dashboard.onrender.com"
echo ""
echo "📖 For detailed instructions, see RENDER_DEPLOYMENT.md"
echo ""
