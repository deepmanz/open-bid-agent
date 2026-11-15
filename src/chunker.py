import pymupdf


def load_pages(pdf_path):
    """Read the PDF and return a list of page texts, with blank lines tidied."""
    doc = pymupdf.open(pdf_path)
    pages = []
    for page in doc:
        text = page.get_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        pages.append("\n".join(lines))
    return pages


def make_chunks(pages, pages_per_chunk=4, overlap=1):
    """Group pages into chunks, overlapping by one page so no requirement is cut in half."""
    chunks = []
    step = pages_per_chunk - overlap
    for start in range(0, len(pages), step):
        group = pages[start:start + pages_per_chunk]
        chunks.append({
            "pages": f"{start + 1}-{start + len(group)}",
            "text": "\n\n".join(group),
        })
        if start + pages_per_chunk >= len(pages):
            break
    return chunks


if __name__ == "__main__":
    pages = load_pages("data/gwinnett-rp027-25.pdf")
    chunks = make_chunks(pages)
    print(f"{len(pages)} pages -> {len(chunks)} chunks\n")
    for c in chunks:
        print(f"Pages {c['pages']}: {len(c['text']):,} characters")