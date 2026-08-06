from backend.documents.pdf_service import extract_text_from_pdf
from backend.documents.chunking import split_text
from backend.documents.pdf_vector_store import build_pdf_index, search_pdf

text = extract_text_from_pdf("sample.pdf")
chunks = split_text(text)

build_pdf_index(chunks)

query = "What programming languages do I know?"

results = search_pdf(query)

print("Search Results:\n")

for i, result in enumerate(results, 1):
    print(f"Result {i}")
    print(result)
    print("-" * 60)