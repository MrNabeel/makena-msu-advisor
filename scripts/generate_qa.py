"""
generate_qa.py — turn scraped policy text into structured Q&A pairs with Claude.

Representative reconstruction of the Q&A-generation step in the Makena pipeline
(INFO 401, Spring 2026). It reads the cleaned knowledge-base text, sends each
chunk to the Claude API, and asks for grounded question/answer pairs that stay
strictly inside the provided source — the same groundedness discipline that the
final benchmark scored.

The API key is read from the environment (never hardcoded). Copy .env.example
to .env and set ANTHROPIC_API_KEY, or export it in your shell.
"""

import os
import sys

from anthropic import Anthropic

MODEL = "claude-opus-4-8"   # latest Claude model id at time of writing
KB_FILE = "msu_kb_export.txt"
OUTPUT_FILE = "generated_qa.md"

SYSTEM = (
    "You convert university policy text into question/answer pairs for an "
    "academic-advising knowledge base. Rules: (1) Use ONLY facts present in the "
    "provided source text — never add outside knowledge. (2) If the source does "
    "not support an answer, skip it. (3) Keep each answer concise and include the "
    "source URL when it appears in the text. (4) Do not mix undergraduate and "
    "graduate policies in a single pair."
)

PROMPT_TEMPLATE = (
    "From the source text below, generate up to 5 grounded Q&A pairs a student "
    "might ask an academic advisor. Format each as:\n"
    "Q: <question>\nA: <answer with source link if present>\n\n"
    "SOURCE TEXT:\n{chunk}"
)


def read_chunks(path):
    """Yield each [SOURCE]-delimited chunk written by scrape_msu.py."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for block in text.split("--- [END SOURCE] ---"):
        block = block.strip()
        if block:
            yield block


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Set ANTHROPIC_API_KEY (see .env.example) before running.")
    if not os.path.exists(KB_FILE):
        sys.exit(f"Run scrape_msu.py first — {KB_FILE} not found.")

    client = Anthropic(api_key=api_key)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for i, chunk in enumerate(read_chunks(KB_FILE), start=1):
            resp = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM,
                messages=[{"role": "user",
                           "content": PROMPT_TEMPLATE.format(chunk=chunk)}],
            )
            out.write(resp.content[0].text.strip() + "\n\n")
            print(f"  ✓ generated Q&A from chunk {i}")

    print(f"  ✓ wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
