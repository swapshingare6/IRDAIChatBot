import os
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import PARSED_DIR, VECTOR_DB_DIR

def embed_node(state):
    print("🧠 Embedding documents...")
    try:
        docs = []
        for filename in os.listdir(PARSED_DIR):
            if filename.endswith(".txt"):
                loader = TextLoader(os.path.join(PARSED_DIR, filename), encoding="utf-8")
                docs.extend(loader.load())

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(docs)

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=OpenAIEmbeddings(),
            persist_directory=VECTOR_DB_DIR
        )
        vectorstore.persist()
        return {"embed_done": True}
    except Exception as e:
        return {"error": f"Embedding failed: {e}"}
