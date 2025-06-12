# suggest_agent.py
import re
from llm_provider import llm
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load your model (adjust if needed)
template = """You are an assistant helping users interact with IRDA insurance regulations.
Based on the assistant's previous answer, suggest 3 to 5 follow-up questions in 4-5 words which the user might ask next.

Answer:
{answer}

Suggested Questions:"""

suggest_prompt = PromptTemplate.from_template(template)
suggest_chain = LLMChain(llm=llm, prompt=suggest_prompt)

def generate_suggestions(answer: str) -> list[str]:
    output = suggest_chain.run(answer=answer)

    return [
        re.sub(r"^[\d\.\-\•\s]+", "", q).strip()
        for q in output.strip().split("\n")
        if q.strip()
    ]
