import PyPDF2
import io

def extract_text_from_pdf(pdf_content):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() or ""
    return text
