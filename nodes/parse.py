import os
import pdfplumber
from config import RAW_DIR, PARSED_DIR

def parse_node(state):
    print("📄 Parsing documents...")
    os.makedirs(PARSED_DIR, exist_ok=True)

    try:
        for filename in os.listdir(RAW_DIR):
            if not filename.endswith(".pdf"):
                continue
            input_path = os.path.join(RAW_DIR, filename)
            output_path = os.path.join(PARSED_DIR, filename.replace(".pdf", ".txt"))
            if os.path.exists(output_path):
                continue

            with pdfplumber.open(input_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

        return {"parse_done": True}
    except Exception as e:
        return {"error": f"Parsing failed: {e}"}
