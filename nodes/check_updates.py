import os
from config import RAW_DIR

def check_node(state):
    print("✅ Checking for update...")
    if not os.listdir(RAW_DIR):  # First run or reset
        return {}

    # You could also check if files are older than X days, or scrape new file list
    return {"skip_scrape": False}
