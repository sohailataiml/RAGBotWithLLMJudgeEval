import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

pdf_files = [
    "ProteinEfficiencyRatio-FinalGuidance-May2026.pdf",
    "56628397dftrv1 - Drug and Device Manufacturer Communications With Payors Q&A.pdf",
    "Guidance-Human-Factors-Marketing.pdf",
    "Master Protocols Rev Draft Guidance for Industry.pdf"
]

llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.3)

qa_pairs = []

for pdf_path in pdf_files:
    print(f"\nProcessing {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    # Take first 5 pages of each document
    sample_pages = documents[:5]
    context = "\n\n".join([f"Page {doc.metadata.get('page', 'Unknown')}:\n{doc.page_content[:2000]}" for doc in sample_pages])
    
    prompt = f"""Based on the following document excerpts, generate 5 diverse question-answer pairs for RAG evaluation.

Document: {pdf_path}

Content:
{context}

Generate 5 Q&A pairs in JSON format:
[
  {{"question": "...", "answer": "...", "document": "{pdf_path}"}},
  ...
]

Requirements:
- Questions should be specific and answerable from the content
- Answers should be concise (2-4 sentences)
- Include different question types (factual, conceptual, procedural)
- Questions should test retrieval quality

Output only valid JSON:"""
    
    response = llm.invoke(prompt)
    try:
        content = response.content
        # Try to extract JSON from markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        pairs = json.loads(content)
        qa_pairs.extend(pairs)
        print(f"Generated {len(pairs)} Q&A pairs")
    except Exception as e:
        print(f"Failed to parse response for {pdf_path}: {e}")
        print(f"Response content: {response.content[:500]}")

# Save to file
with open('rag_evaluation_qa.json', 'w') as f:
    json.dump(qa_pairs, f, indent=2)

print(f"\nTotal Q&A pairs generated: {len(qa_pairs)}")
print("Saved to rag_evaluation_qa.json")
