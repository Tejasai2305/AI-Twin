from backend.documents.pdf_service import extract_text_from_pdf
from backend.documents.chunking import split_text

text = extract_text_from_pdf("sample.pdf")

chunks = split_text(text)

print("Total Chunks:", len(chunks))

print("\nFirst Chunk:\n")
print(chunks[0])