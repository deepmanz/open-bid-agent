import difflib
import json
import re
import ollama
from chunker import load_pages, make_chunks

MODEL = "llama3.1:8b"
LIST_KEYS = ["scope", "key_dates", "submission_rules", "mandatory_requirements", "evaluation_criteria"]

SYSTEM_PROMPT = (
    "You are an RFP analyst at an IT services company that responds to client RFPs. "
    "Extract facts ONLY from the RFP text you are given. Never guess, invent or use templates. "
    "For every item, copy a short exact quote from the text as evidence."
)

TASK_TEMPLATE = """From this section of an RFP, return JSON with exactly these keys:
{
  "client": "issuing organisation (leave blank if not stated)",
  "rfp_number": "RFP reference number (leave blank if not stated)",
  "scope": [{"text": "work the client wants done", "quote": "exact words from the text"}],
  "key_dates": [{"event": "what happens", "date": "when", "quote": "exact words from the text"}],
  "submission_rules": [{"text": "how, where, format of submission", "quote": "exact words from the text"}],
  "mandatory_requirements": [{"text": "what the vendor MUST have or do", "quote": "exact words from the text"}],
  "evaluation_criteria": [{"criterion": "what is scored", "weight": "points or percent if stated", "quote": "exact words from the text"}]
}
Rules:
- Only include items that actually appear in this text. If a section has nothing here, return [].
- Each "quote" must be copied word for word from the text, 5 to 25 words long.
- Standard legal terms, insurance types and contract conditions are NOT scope.

RFP pages PAGES:
---
TEXT
---"""


def normalize(text):
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def is_grounded(quote, source):
    """Deterministic check: does the quote really appear in the source text (allowing tiny differences)?"""
    q = normalize(quote)
    if len(q) < 10:
        return False
    if q in source:
        return True
    match = difflib.SequenceMatcher(None, source, q, autojunk=False).find_longest_match(
        0, len(source), 0, len(q))
    return match.size / len(q) >= 0.8


def extract_chunk(chunk):
    """LLM extracts facts with quotes; code keeps only the ones whose quote is found in the chunk."""
    task = TASK_TEMPLATE.replace("PAGES", chunk["pages"]).replace("TEXT", chunk["text"])
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": task}],
        format="json",
        options={"temperature": 0, "num_ctx": 8192},
    )
    result = json.loads(response["message"]["content"])

    source = normalize(chunk["text"])
    rejected = []
    for key in LIST_KEYS:
        kept = []
        for item in result.get(key) or []:
            if isinstance(item, dict) and is_grounded(item.get("quote", ""), source):
                kept.append(item)
            else:
                rejected.append({"section": key, "item": item})
        result[key] = kept
    result["_rejected"] = rejected
    return result


if __name__ == "__main__":
    chunks = make_chunks(load_pages("data/gwinnett-rp027-25.pdf"))
    first = chunks[0]
    print(f"Extracting from pages {first['pages']}...\n")
    result = extract_chunk(first)
    print(json.dumps(result, indent=2, ensure_ascii=False))