# Architecture

Makena is a RAG (Retrieval-Augmented Generation) chatbot deployed on **Chatbase** (GPT-4o Mini). The interesting engineering isn't the model — it's the data pipeline that feeds it and the prompt that constrains it.

```
 MSU web pages
      │
      ▼
┌──────────────────────┐
│  Python scrape layer  │   async, rate-limited, domain-bounded, DOM-cleaned
└──────────────────────┘
      │  cleaned text + [SOURCE: url] metadata
      ▼
┌──────────────────────┐
│   Data silos (KB)     │   UG policies | Grad policies | Registrar/standing
└──────────────────────┘
      │  + hand-authored Q&A for gaps (e.g. prerequisites)
      ▼
┌──────────────────────┐
│  Chatbase (RAG)       │   retrieval + GPT-4o Mini
│  + hardened prompt    │   isolation rules, routing, disclaimer
└──────────────────────┘
      │
      ▼
   Student
```

## 1. Scrape layer

A targeted scraper, not a generic crawler. The two representative scripts in [`../scripts/`](../scripts/) show the core patterns; the original project split the work across a few specialized scripts:

| Component | Job |
|---|---|
| `advanced_scrape.py` | Targeted scrape of a fixed list of high-value URLs, with keyword relevance scoring and prerequisite/GPA pattern extraction. |
| `deep_crawler.py` | BFS recursive crawler that scores pages by academic-keyword density (prerequisites, GPA, retention, course codes) and follows only the promising ones. |
| `pdf_hunter.py` | Discovers and downloads linked PDFs from MSU pages. |
| `department_scraper.py` | Business-school department deep-dive that follows sub-page links. |
| `qa_generator.py` | Sends cleaned text to the Claude API to auto-generate structured Q&A pairs. |
| `qa_enhancer.py` | Targeted gap-filler that generates Q&A pairs for knowledge gaps found during testing. |

The engineering patterns that mattered (all shown in [`../scripts/scrape_msu.py`](../scripts/scrape_msu.py)):

- **Async concurrency** — `aiohttp.ClientSession` + `asyncio.gather(*tasks)`: pages fetch concurrently but compile in a deterministic order.
- **Rate limiting** — `asyncio.Semaphore(2)`: never more than two simultaneous hits, so a home connection isn't flagged by the university firewall.
- **Fault tolerance** — `tenacity` `@retry(wait=wait_exponential(...), stop=stop_after_attempt(3))`: a dropped socket retries with exponential backoff instead of killing the run.
- **Domain bounding** — `urljoin(start, href).split('#')[0]` normalizes relative links and drops anchors; `if ALLOWED_DOMAIN in url` keeps the spider on the Feliciano domain.
- **DOM cleansing** — `soup(["script","style","nav","footer","header","aside"])` → `.extract()` deletes structural noise before saving, cutting token bloat.
- **Storage guard** — `os.path.getsize(file) > max_bytes` enforces the Chatbase 10 MB tier limit.

## 2. Citation metadata

Every saved chunk is wrapped so the LLM can cite where a fact came from:

```
--- [SOURCE: https://www.montclair.edu/business/... ] ---
<clean policy text>
--- [END SOURCE] ---
```

This is what lets Makena attach a verifiable MSU link to its answers — a hard requirement from the advisor discovery meeting.

## 3. Data silos (the fix for "data bleed")

The most important architectural decision. A single monolithic knowledge file caused the model to blend undergraduate and graduate policies (see [`benchmarking.md`](benchmarking.md)). Splitting the knowledge base into **isolated files** — Undergraduate Policies, Graduate Policies, Registrar/Academic Standing — plus a strict isolation rule in the system prompt eliminated the crossover.

Course prerequisites aren't published on public MSU pages, so a small set of Q&A pairs was hand-authored and loaded via Chatbase's Q&A / text-snippet tabs.

## 4. Deployment

- **Chatbase Help Page** — a standalone, ChatGPT-style interface, public and no-login.
- **Pre-routing welcome message** classifies the student (Undergraduate / Graduate / Transfer) before answering, reinforcing the silo separation.
- **Suggested prompts** for the top tasks (registration, advising appointment, GPA check).
- **Navigate booking** is hardcoded in the system prompt so any appointment query routes straight to the EAB Navigate URL.
- **AI disclaimer** is shown every session and repeated on responses.
