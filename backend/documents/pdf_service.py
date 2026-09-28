import fitz


def extract_text_from_pdf(file_path):
    document = None

    try:
        document = fitz.open(file_path)

        if document.is_encrypted:
            raise ValueError("The PDF is password-protected.")

        text = ""

        for page in document:
            text += page.get_text()

        if not text.strip():
            raise ValueError("The PDF does not contain extractable text.")

        return text

    except fitz.FileDataError:
        raise ValueError("The uploaded file is not a valid PDF.")

    except ValueError:
        raise

    except Exception as e:
        print("PDF extraction error:", e)
        raise ValueError("Unable to extract text from the PDF.")

    finally:
        if document is not None:
            document.close()