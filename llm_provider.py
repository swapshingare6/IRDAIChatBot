from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
import os

load_dotenv()  # reads /home/ubuntu/irdai_apis/.env

model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set in .env")

# Shared, deterministic instance
llm = ChatOpenAI(
    model=model_name,
    temperature=temperature,
    openai_api_key=api_key
)