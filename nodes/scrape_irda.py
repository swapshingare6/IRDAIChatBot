import os
import re
import time
import asyncio
import hashlib
import requests
import langid
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from config import RAW_DIR

IRDA_BASE_URL = "https://irdai.gov.in"
DOWNLOADABLE_EXTENSIONS = [".pdf", ".doc", ".docx"]

def sanitize_filename(name: str) -> str:
    name = re.sub(r'^[a-f0-9]{6}_', '', name)
    name = re.sub(r'[<>:"/\\|?*\n]', "_", name.strip())
    return name

def is_english_content(text: str, threshold: float = 0.8) -> bool:
    if not text.strip():
        return False
    try:
        lang, confidence = langid.classify(text)
        return lang == 'en' and confidence >= threshold
    except:
        return True

def get_title_from_link_tag(tag):
    try:
        parent = tag.find_parent(["tr", "div"])
        text_parts = [t.strip() for t in parent.stripped_strings if t.strip()]
        full_text = " ".join(text_parts)
        return sanitize_filename(full_text[:80])
    except:
        return ""

def strip_query_params(url):
    parsed = urlparse(url)
    return parsed.path

def ascii_fallback(text: str) -> str:
    try:
        return text.encode("ascii", "ignore").decode("ascii")
    except:
        return text

def unique_filename_from_title(title, url):
    clean_path = strip_query_params(url)
    original_filename = os.path.basename(clean_path)
    ext = os.path.splitext(clean_path)[1]

    # Default to .pdf if no extension found
    if not ext:
        ext = ".pdf"

    ascii_title = ascii_fallback(title)
    safe_title = sanitize_filename(ascii_title)

    # If no usable title, fallback to original filename (but ensure it has an extension)
    if not safe_title.strip():
        fallback_name = sanitize_filename(original_filename)
        if not fallback_name.endswith(ext):
            fallback_name += ext
        return fallback_name

    return f"{safe_title}{ext}"

async def scrape_irda_circulars(state: dict) -> dict:
    start_urls = state.get("start_urls", [])
    filter_non_english = state.get("filter_non_english", False)
    if not start_urls:
        return {"error_msg": "No start_urls provided"}

    os.makedirs(RAW_DIR, exist_ok=True)
    total_skipped = 0
    total_downloaded = 0
    page_limit = 1000

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()

        for url in start_urls:
            print(f"\n🚀 Starting scrape for: {url}")
            await page.goto(url)
            page_count = 1

            while True:
                if page_count > page_limit:
                    print("📌 Reached max page limit — stopping.")
                    break

                print(f"\n🔄 Page {page_count} of {url}")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)

                soup = BeautifulSoup(await page.content(), "html.parser")
                anchors = soup.find_all("a", href=True)
                print(f"🔗 Found {len(anchors)} anchor tags")

                links = []
                for a in anchors:
                    href = a['href'].strip()
                    if any(ext in href.lower() for ext in DOWNLOADABLE_EXTENSIONS):
                        full_url = urljoin(IRDA_BASE_URL, href)
                        title = get_title_from_link_tag(a)
                        filename = unique_filename_from_title(title, full_url)
                        links.append((full_url, filename, url))

                print(f"📄 Found {len(links)} document links")

                for link, filename, source_url in links:
                    filepath = os.path.join(RAW_DIR, filename)
                    if os.path.exists(filepath):
                        print(f"ℹ️ Skipping existing file: {filename}")
                        continue

                    try:
                        with requests.get(link, timeout=30, stream=True) as r:
                            r.raise_for_status()

                            if filter_non_english and link.lower().endswith(".pdf"):
                                content_sample = b''.join([chunk for _, chunk in zip(range(2), r.iter_content(2048))])
                                text_sample = content_sample.decode('utf-8', errors='ignore')
                                if not is_english_content(text_sample):
                                    total_skipped += 1
                                    print(f"🚫 Skipped non-English: {filename}")
                                    continue

                            with open(filepath, "wb") as f:
                                for chunk in r.iter_content(8192):
                                    f.write(chunk)

                        print(f"⬇️ Downloaded: {filename}")
                        total_downloaded += 1

                    except Exception as e:
                        print(f"❌ Failed to download {link}: {e}")

                # Pagination
                try:
                    old_html = await page.content()
                    patterns = ["Next", ">", "›", "»"]
                    next_found = False

                    for label in patterns:
                        # Try exact match and case-insensitive match
                        next_buttons = page.locator(f'a:has-text("{label}")')
                        count = await next_buttons.count()
                        for i in range(count):
                            next_button = next_buttons.nth(i)
                            if await next_button.is_visible():
                                await next_button.scroll_into_view_if_needed()
                                await next_button.click()
                                await page.wait_for_timeout(2000)
                                new_html = await page.content()
                                if new_html != old_html:
                                    next_found = True
                                    page_count += 1
                                    break
                        if next_found:
                            break

                    if not next_found:
                        print("✅ No next button found. Pagination ended.")
                        break

                except Exception as e:
                    print(f"❌ Pagination error: {e}")
                    break

        await browser.close()

    return {
        "is_scrape_done": True,
        "skipped_non_english": total_skipped if filter_non_english else 0,
        "total_downloaded": total_downloaded,
        "start_urls_count": len(start_urls)
    }

# To run: asyncio.run(scrape_irda_circulars({...}))
