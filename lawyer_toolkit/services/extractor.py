import pdfplumber
import docx

MAX_CHARS = 40000

def extract_text(uploaded_file):
    filename = uploaded_file.name.lower()
    text = ""
    
    if filename.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif filename.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif filename.endswith(".txt"):
        text = uploaded_file.getvalue().decode("utf-8")
    else:
        raise ValueError("صيغة الملف غير مدعومة.")

    text = text.strip()
    
    if not text:
        raise ValueError("لم يتم العثور على نص. إذا كان هذا ملف PDF ممسوح ضوئياً، فيرجى تحويله باستخدام OCR أولاً.")

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        text += "\n\n[تحذير: تم اقتطاع النص لأنه تجاوز الحد الأقصى المسموح به]"
        
    return text
