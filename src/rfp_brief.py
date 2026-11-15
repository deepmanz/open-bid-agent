import json
from pathlib import Path
from chunker import load_pages, make_chunks
from extractor import extract_chunk

PDF_PATH = "data/gwinnett-rp027-25.pdf"
OUTPUT_DIR = Path("data/output")
TEXT_LISTS = ["scope", "submission_rules", "mandatory_requirements"]


def clean(value):
    text = str(value).strip()
    placeholders = {"", "empty", "blank", "none", "n/a", "null", "not stated", "not specified"}
    return "" if text.lower() in placeholders else text


def merge(results):
    """Combine chunk results: remove exact duplicates, keep each item's quote and page range."""
    brief = {"client": "", "rfp_number": "", "scope": [], "key_dates": [],
             "submission_rules": [], "mandatory_requirements": [], "evaluation_criteria": []}
    rejected, seen = [], set()

    for pages, r in results:
        for key in ("client", "rfp_number"):
            if not brief[key]:
                brief[key] = clean(r.get(key, ""))

        for entry in r.get("_rejected", []):
            rejected.append({**entry, "source_pages": pages})

        for key in TEXT_LISTS:
            for item in r.get(key, []):
                text = clean(item.get("text", ""))
                signature = (key, text.lower())
                if text and signature not in seen:
                    seen.add(signature)
                    brief[key].append({"text": text, "quote": item.get("quote", ""), "source_pages": pages})

        for item in r.get("key_dates", []):
            event, date = clean(item.get("event", "")), clean(item.get("date", ""))
            signature = ("date", event.lower(), date.lower())
            if event and signature not in seen:
                seen.add(signature)
                brief["key_dates"].append({"event": event, "date": date,
                                           "quote": item.get("quote", ""), "source_pages": pages})

        for item in r.get("evaluation_criteria", []):
            criterion, weight = clean(item.get("criterion", "")), clean(item.get("weight", ""))
            signature = ("criterion", criterion.lower())
            if criterion and signature not in seen:
                seen.add(signature)
                brief["evaluation_criteria"].append({"criterion": criterion, "weight": weight,
                                                     "quote": item.get("quote", ""), "source_pages": pages})
    return brief, rejected


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    chunks = make_chunks(load_pages(PDF_PATH))

    results, failures = [], []
    for i, chunk in enumerate(chunks, start=1):
        print(f"[{i}/{len(chunks)}] pages {chunk['pages']}...")
        try:
            results.append((chunk["pages"], extract_chunk(chunk)))
        except Exception as error:
            print(f"    skipped: {error}")
            failures.append(chunk["pages"])

    brief, rejected = merge(results)

    (OUTPUT_DIR / "rfp_brief.json").write_text(
        json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT_DIR / "rejected_items.json").write_text(
        json.dumps(rejected, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nClient: {brief['client']}  |  RFP: {brief['rfp_number']}")
    for key in ["scope", "key_dates", "submission_rules", "mandatory_requirements", "evaluation_criteria"]:
        print(f"  {key}: {len(brief[key])} kept")
    print(f"  rejected (quote not found in RFP): {len(rejected)}")
    if failures:
        print(f"Chunks that failed: {failures}")