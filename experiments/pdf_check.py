import pymupdf

doc = pymupdf.open("data/gwinnett-rp027-25.pdf")
print(f"Pages: {doc.page_count}")

text = "".join(page.get_text() for page in doc)
print(f"Characters of text: {len(text)}")
print("\n--- First 1,500 characters ---\n")
print(text[:1500])