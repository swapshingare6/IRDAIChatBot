import os
import mimetypes
from dotenv import load_dotenv
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import RAW_DIR, VECTORSTORE_DIR
import tiktoken
from typing import List

load_dotenv()  # Ensure OPENAI_API_KEY is loaded

MAX_TOKENS_PER_BATCH = 250_000  # Safe batch size (under 300K OpenAI limit)

def is_pdf_file(filepath):
    mime_type, _ = mimetypes.guess_type(filepath)
    return mime_type == 'application/pdf'


def get_token_count(text: str, model_name="text-embedding-ada-002") -> int:
    enc = tiktoken.encoding_for_model(model_name)
    return len(enc.encode(text))


def batch_chunks_by_token_limit(chunks, max_tokens=MAX_TOKENS_PER_BATCH) -> List[List]:
    enc = tiktoken.encoding_for_model("text-embedding-ada-002")
    batches = []
    current_batch = []
    current_tokens = 0

    for chunk in chunks:
        tokens = len(enc.encode(chunk.page_content))

        if current_tokens + tokens > max_tokens:
            batches.append(current_batch)
            current_batch = [chunk]
            current_tokens = tokens
        else:
            current_batch.append(chunk)
            current_tokens += tokens

    if current_batch:
        batches.append(current_batch)

    return batches


def load_and_embed_pdfs():
    all_docs = []

    # --- Load all PDF files ---
    for fname in os.listdir(RAW_DIR):
        if not fname.lower().endswith(".pdf"):
            continue

        path = os.path.join(RAW_DIR, fname)
        if not is_pdf_file(path):
            print(f"❌ Skipping non-PDF file: {fname}")
            continue

        try:
            loader = PyMuPDFLoader(path)
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = fname  # Add source metadata
            
            all_docs.extend(docs)
            
            print(f"📄 Loaded {len(docs)} pages from {fname}")
        except Exception as e:
            print(f"❌ Failed to load {fname}: {e}")

    print(f"\n📚 Total pages loaded: {len(all_docs)}")

    # --- Chunk documents safely ---
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(all_docs)
    print(f"🔹 Split into {len(chunks)} chunks")

    # --- Group chunks into safe token batches ---
    token_batches = batch_chunks_by_token_limit(chunks)
    print(f"🔄 Chunked into {len(token_batches)} safe token batches")

    # --- Embed each batch separately ---
    embeddings = OpenAIEmbeddings()
    vectordb = Chroma(embedding_function=embeddings, persist_directory=VECTORSTORE_DIR)

    for i, batch in enumerate(token_batches):
        print(f"🚀 Embedding batch {i+1}/{len(token_batches)} with {len(batch)} chunks")
        vectordb.add_documents(batch)
        vectordb._client.persist()  # Save to disk after each batch

    print(f"✅ All batches embedded and saved to: {VECTORSTORE_DIR}")


if __name__ == "__main__":
    load_and_embed_pdfs()
