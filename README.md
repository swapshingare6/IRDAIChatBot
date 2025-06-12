# IRDAIChatBot

Have you ever struggled to find the latest circular or regulation from the **IRDAI (Insurance Regulatory and Development Authority of India)** website?

So did I — and that’s why I decided to **build a full-stack AI-powered chatbot** that can:
- Scrape circulars and press notes from the IRDAI website
- Extract and embed content from PDFs/HTML
- Answer user questions with accurate regulatory information
- Suggest follow-up questions like a real assistant
- Provide a beautiful and modern UI using Angular + Bootstrap

In this blog, I’ll walk through the **architecture**, **tech stack**, and some **cool agentic automation** behind the scenes.

---

## 🚀 Overview: What I Built

**The IRDAI Chatbot** is a fully automated system that:
1. **Scrapes and downloads** IRDAI circulars across all paginated pages
2. **Parses and embeds** PDFs using LangChain + OpenAI embeddings
3. Stores the embeddings in a local **Chroma vectorstore**
4. Uses a smart LangChain QA Agent to answer questions using RAG (retrieval-augmented generation)
5. Offers an interactive, smooth **Angular frontend** with live chat, typing effects, suggestion bubbles, and animated scroll
6. Suggests relevant follow-up questions based on each answer!

---

## 🧰 Tech Stack

| Layer | Tech |
|------|------|
| 🧠 LLM | OpenAI GPT-4 via LangChain |
| 🧱 Vectorstore | ChromaDB |
| 📚 Embedding | `OpenAIEmbeddings` |
| 🔍 RAG | LangChain QA chains |
| 🧩 Agent Framework | LangGraph |
| 🔧 Backend | FastAPI |
| 🧼 PDF Parsing | PyMuPDF |
| 🌐 Frontend | Angular 17 + Bootstrap 5 |
| 🤖 Scraping | Selenium + BeautifulSoup |
| 🔁 Async | Python `asyncio` + batching |

---

## 🧠 Backend: AI Agent Architecture

I built a smart multi-step LangGraph agent with these nodes:

1. **Scrape Node** — uses Selenium to crawl all IRDAI circular pages, follows paginated "Next" links, and downloads PDFs
2. **Parse Node** — uses PyMuPDF to read PDF content
3. **Embed Node** — splits content into chunks and stores embeddings in Chroma
4. **QA Node** — answers questions by retrieving relevant docs using vector similarity
5. **Suggestion Node** — uses another agent to suggest follow-up questions based on the bot's answer

All nodes are reusable and callable as standalone FastAPI routes too.

---

## 🧠 Chatbot Flow: How Everything Connects

Here’s a visual flow of how the chatbot works — from user input to AI agents performing RAG-based document search and response formatting:

![IRDAI Chatbot Flow Diagram](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/pdqtliip0nfzj075q5dl.png)


- **Text Input:** User submits a question.
- **ChatGPT Core:** Formats the query, routes it to agents.
- **AI Agents:**
  - `Scraper`: Collects PDFs & press notes
  - `ETL`: Parses and embeds documents
  - `QA`: Handles similarity search + answer generation
- **Database:** Stores and retrieves document embeddings
- **Chat Interface:** Formats HTML responses and suggestions

This modular design ensures scalability and clarity.

---

## ⚙️ Smart Features

- ✅ **Async batching for large document QA** (splits input across token-safe chunks)
- ✅ **Automatic spell correction + similar question detection**
- ✅ **Answer caching** to improve performance with a time-aware LRU-like strategy
- ✅ **Suggestions engine** that generates related follow-up questions using a second LLM chain
- ✅ **Common `llm_provider.py`** to centralize LLM configuration across the app

---

## 💬 Frontend: Angular Chat UI

The frontend is built with **Angular 17 standalone components**, styled with **Bootstrap 5**, and includes:

- 💡 Suggested questions before and after answers
- 🤖 Typing animation (blinking dots)
- 🎯 Smart session tracking using UUIDs
- 🔄 Smooth scroll-to-bottom on every update
- ❌ Graceful error handling
- 🔥 Responsive, mobile-friendly layout


---

## 🌐 FastAPI Backend

The backend exposes:
- `/ask` — main QA endpoint
- `/suggest` — generate follow-up questions
- `/scrape` — run scraper
- `/embed` — re-embed new content

You can trigger scraping + embedding via the LangGraph agent, CLI, or API — fully flexible.

---

## 🧠 Example Q&A

**Q:** What is Saral Jeevan Bima?

**A:** Saral Jeevan Bima is a standard term life insurance policy mandated by IRDAI...

**Suggested follow-ups:**
- "Who is eligible for Saral Jeevan?"
- "Is it mandatory for insurers?"
- "What are the premium limits?"

---

## 💡 Lessons Learned

- 🔍 **LangGraph is amazing** for building modular multi-step agent flows.
- ⚠️ Be cautious of OpenAI token limits — I had to chunk documents smartly.
- 🔄 Building a good **frontend experience is just as important** as the backend logic.
- ⚡ Don’t forget **caching** when dealing with repeated queries or expensive operations.

---

## 🎁 What's Next

- Add user authentication for session history
- Push updates to a Firebase or Netlify-hosted frontend
- Enable upload of user PDFs for comparison
- Train a custom model on domain-specific terms

---

## 📦 Repo Coming Soon

Planning to open-source this soon. Let me know if you’d like early access!

---

## 🙌 Let’s Connect!

If you found this useful or have feedback:

💬 Comment below  
🧠 Follow me on [LinkedIn](www.linkedin.com/in/swapnil-shingare)  
💡 Have a chatbot idea? Let’s collaborate!
