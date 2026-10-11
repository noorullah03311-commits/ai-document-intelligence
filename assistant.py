"""Local, source-grounded document Q&A using TF-IDF retrieval (no external API)."""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import get_all_documents

MIN_RELEVANCE_SCORE = 0.06
MAX_CHUNK_CHARS = 700
CHUNK_OVERLAP_CHARS = 100


def chunk_text(text, max_chars=MAX_CHUNK_CHARS, overlap=CHUNK_OVERLAP_CHARS):
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            boundary = text.rfind(" ", start + max_chars // 2, end)
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def answer_question(question, documents=None, top_k=3):
    question = (question or "").strip()
    if not question:
        return {"answer": "Please enter a question.", "sources": []}
    documents = get_all_documents() if documents is None else documents
    chunks, metadata = [], []
    for document in documents:
        text = document.get("full_text") or document.get("text_preview") or ""
        for chunk in chunk_text(text):
            chunks.append(chunk)
            metadata.append({
                "document_id": document.get("id", "Unknown"),
                "filename": document.get("original_filename", "Unknown document"),
                "text": chunk,
            })
    if not chunks:
        return {"answer": "The available documents do not contain enough readable text to answer this question.", "sources": []}
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        matrix = vectorizer.fit_transform(chunks + [question])
    except ValueError:
        return {"answer": "The available documents do not contain enough information to answer this question.", "sources": []}
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    ranked = sorted(range(len(scores)), key=lambda idx: float(scores[idx]), reverse=True)
    sources = []
    for idx in ranked[:max(1, top_k)]:
        score = float(scores[idx])
        if score < MIN_RELEVANCE_SCORE:
            continue
        source = dict(metadata[idx])
        source["score"] = score
        sources.append(source)
    if not sources:
        return {"answer": "I couldn't find enough supporting information in the available documents to answer that question.", "sources": []}
    excerpts = "\n\n".join(f"[{i}] {source['text']}" for i, source in enumerate(sources, start=1))
    answer = "I found these relevant passages. Use the source references to verify the details; this local assistant returns evidence excerpts rather than generating unsupported claims.\n\n" + excerpts
    return {"answer": answer, "sources": sources}
