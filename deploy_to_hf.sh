#!/bin/bash

# Hugging Face Space Deployment Script for RAG Chat Bot

echo "🚀 Deploying RAG Chat Bot to Hugging Face Spaces"
echo "================================================"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    exit 1
fi

# Check if Hugging Face CLI is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "⚠️  Hugging Face CLI not found. Installing..."
    pip install huggingface_hub
fi

# Prompt for Hugging Face token
echo ""
echo "Please provide your Hugging Face token:"
echo "(Get it from: https://huggingface.co/settings/tokens)"
read -sp "HF Token: " HF_TOKEN
echo ""

# Prompt for space name
echo ""
echo "Enter your Hugging Face username:"
read HF_USERNAME

SPACE_NAME="RAGBotWithLLMJudgeEval"
SPACE_URL="https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"

echo ""
echo "📦 Preparing files for deployment..."

# Create a temporary directory for deployment
DEPLOY_DIR="hf_space_deploy"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Copy necessary files
echo "Copying files..."
cp app.py $DEPLOY_DIR/
cp requirements_hf.txt $DEPLOY_DIR/requirements.txt
cp README_HF.md $DEPLOY_DIR/README.md
cp .env.example $DEPLOY_DIR/ 2>/dev/null || true

# Copy PDF files
cp "ProteinEfficiencyRatio-FinalGuidance-May2026.pdf" $DEPLOY_DIR/ 2>/dev/null || echo "⚠️  PDF 1 not found"
cp "56628397dftrv1 - Drug and Device Manufacturer Communications With Payors Q&A.pdf" $DEPLOY_DIR/ 2>/dev/null || echo "⚠️  PDF 2 not found"
cp "Guidance-Human-Factors-Marketing.pdf" $DEPLOY_DIR/ 2>/dev/null || echo "⚠️  PDF 3 not found"
cp "Master Protocols Rev Draft Guidance for Industry.pdf" $DEPLOY_DIR/ 2>/dev/null || echo "⚠️  PDF 4 not found"

# Copy evaluation files if they exist
cp rag_evaluation_qa.json $DEPLOY_DIR/ 2>/dev/null || true
cp rag_eval_judge_summary_*.csv $DEPLOY_DIR/ 2>/dev/null || true

cd $DEPLOY_DIR

# Initialize git repository
echo ""
echo "🔧 Initializing git repository..."
git init
git config user.email "deploy@huggingface.co"
git config user.name "HF Deploy"

# Add all files
git add .
git commit -m "Initial deployment of RAG Chat Bot with LLM Judge Eval"

# Add Hugging Face remote
echo ""
echo "🔗 Connecting to Hugging Face Space..."
git remote add space https://${HF_USERNAME}:${HF_TOKEN}@huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}

# Push to Hugging Face
echo ""
echo "⬆️  Pushing to Hugging Face Spaces..."
git push --force space main

cd ..

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Your space will be available at:"
echo "   ${SPACE_URL}"
echo ""
echo "⚙️  Important: Set your ANTHROPIC_API_KEY in Space settings:"
echo "   ${SPACE_URL}/settings"
echo ""
echo "🔐 Add your Anthropic API key as a secret with name: ANTHROPIC_API_KEY"
echo ""
echo "⏳ Note: First build may take 5-10 minutes"
echo ""
