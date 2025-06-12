import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PARSED_DIR = os.path.join(DATA_DIR, "parsed")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vectorstore")
VECTORSTORE_DIR = "data/vectordb"

IRDA_URL = "https://irdai.gov.in/document-category/circulars/"
