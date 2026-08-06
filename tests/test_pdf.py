from backend.documents.pdf_service import extract_text_from_pdf

text = extract_text_from_pdf("sample.pdf")

print(text[:1000])