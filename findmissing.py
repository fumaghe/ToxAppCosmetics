import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# Specifica il percorso all'eseguibile di Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Apri il PDF
pdf_document = 'PDF FOTO.pdf'
pdf = fitz.open(pdf_document)

# Inizializza il contenuto del file di testo estrapolato
extracted_text = ""

# Loop attraverso tutte le pagine
for page_num in range(len(pdf)):
    page = pdf.load_page(page_num)
    pix = page.get_pixmap()
    
    # Converti l'immagine della pagina in PIL Image
    img = Image.open(io.BytesIO(pix.tobytes()))
    
    # Salva l'immagine come temporaneo (opzionale, per verificare il risultato)
    temp_image_path = f"temp_page_{page_num}.png"
    img.save(temp_image_path)
    
    # Esegui OCR sull'immagine
    text = pytesseract.image_to_string(img, lang='eng')  # Specifica la lingua 'eng' per inglese
    
    # Aggiungi il testo estratto al testo complessivo
    extracted_text += text + "\n\n"

# Salva il testo estratto in un file
with open("estrapolato.txt", "w", encoding="utf-8") as text_file:
    text_file.write(extracted_text)

print("Il testo è stato estrapolato con successo e salvato in estrapolato.txt")
