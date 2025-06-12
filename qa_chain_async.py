import os
import tiktoken
import asyncio
import re
from typing import List, Dict
from langchain.schema import Document
from llm_provider import llm, model_name
from langchain.chains.question_answering import load_qa_chain
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from config import VECTORSTORE_DIR

# In-memory session history
session_histories: Dict[str, List[Dict[str, str]]] = {}

# --- Token-safe batch splitter ---
def split_chunks_by_tokens(docs: List[Document], max_tokens=90000):
    enc = tiktoken.encoding_for_model(model_name)
    batches = []
    current_batch = []
    token_count = 0

    for doc in docs:
        tokens = len(enc.encode(doc.page_content))
        if token_count + tokens > max_tokens:
            batches.append(current_batch)
            current_batch = [doc]
            token_count = tokens
        else:
            current_batch.append(doc)
            token_count += tokens

    if current_batch:
        batches.append(current_batch)

    return batches

# --- Async call for a single batch ---
async def ask_batch_async(llm, chain, batch, query):
    loop = asyncio.get_event_loop()

    def run_chain():
        try:
            result = chain.run({"input_documents": batch, "question": query})
            if isinstance(result, dict):
                return result.get("output_text", "")
            return str(result)
        except Exception as e:
            print(f"⚠️ Error in batch QA: {e}")
            return ""

    return await loop.run_in_executor(None, run_chain)

# --- Run all batches in parallel ---
async def ask_all_batches(query: str, docs: List[Document]):
    
    chain_type = "stuff" if len(docs) <= 3 else "map_reduce"
    chain = load_qa_chain(llm, chain_type=chain_type)  # Improved QA method
    batches = split_chunks_by_tokens(docs)

    print(f"🧩 Split into {len(batches)} batches. Processing asynchronously...")
    tasks = [ask_batch_async(llm, chain, batch, query) for batch in batches]
    results = await asyncio.gather(*tasks)

    return [res for res in results if isinstance(res, str) and res.strip()]

# --- Final summarization of all answers + chat history ---
def summarize_answers(session_id: str, query: str, answers: List[str]):
    if not answers:
        return "<p>No relevant information found.</p>"

    history = session_histories.get(session_id, [])
    history_prompt = "\n".join([f"Q: {h['q']}\nA: {h['a']}" for h in history])

    summary_prompt = f"""
    You are an expert assistant on IRDA regulations. Your goal is to write a clear, concise, and helpful answer in HTML format.

    User has asked: "{query}"

    Below are answers from various document excerpts:
    {''.join(f'<p>{a}</p>' for a in answers)}

    Based on these, summarize into one final detailed answer in valid HTML. Avoid repeating sentences. Use <ul>/<li> for lists, and bold key points.
    """
    raw_output = llm.predict(summary_prompt)
    html_answer = raw_output.replace("```html", "").replace("```", "").strip()
    
    return html_answer

# --- Entry point ---
async def ask_irda_question_long(session_id: str, query: str):
    # ✅ Check session history to return cached result
    history = session_histories.get(session_id, [])
    for record in history:
        if record["q"].strip().lower() == query.strip().lower():
            print("⚡ Returning cached answer")
            return {
                "answer": record["a"],
                "sources": record.get("sources", []),
                "partials": record.get("partials", []),
                "source_previews": record.get("source_previews", [])
            }
    print(f"🔍 Processing new query: {query}")
    
    vectordb = Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=OpenAIEmbeddings()
    )
    docs = vectordb.max_marginal_relevance_search(query, k=10, fetch_k=30)
    print(f"📄 Retrieved {len(docs)} documents.")

    # Filter out unhelpful results
    for doc in docs:
        doc.page_content = re.sub(r"(Page \d+ of \d+|IRDAI|IRDA)", "", doc.page_content, flags=re.IGNORECASE)

    print(f"✅ {len(docs)} documents after filtering.")
    for i, doc in enumerate(docs):
        print(f"\n--- Document {i+1} Preview ---\n{doc.page_content[:300]}")

    if not docs:
        return {
            "answer": "No meaningful content found to answer your question.",
            "sources": [],
            "partials": []
        }

    batch_answers = await ask_all_batches(query, docs)
    final_answer = summarize_answers(session_id, query, batch_answers)

    session_histories.setdefault(session_id, []).append({
        "q": query,
        "a": final_answer,
        "sources": list({f"{doc.metadata.get('source', 'unknown')} (page {doc.metadata.get('page', 'n/a')})" for doc in docs}),
        "partials": batch_answers,
        "source_previews": [doc.page_content[:300] for doc in docs]
    })

    return {
        "answer": final_answer,
        "sources": list({f"{doc.metadata.get('source', 'unknown')} (page {doc.metadata.get('page', 'n/a')})" for doc in docs}),
        "source_previews": [doc.page_content[:300] for doc in docs],
        "partials": batch_answers
    }