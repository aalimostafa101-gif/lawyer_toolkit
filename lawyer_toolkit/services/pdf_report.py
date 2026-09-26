import os
import urllib.request
import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import arabic_reshaper
from bidi.algorithm import get_display

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "Amiri-Regular.ttf")

def download_font_if_needed():
    if not os.path.exists(FONT_PATH):
        os.makedirs(FONT_DIR, exist_ok=True)
        try:
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
            return True
        except Exception:
            return False
    return True

def fix_arabic(text: str) -> str:
    """Reshape and apply bidi algorithm for Arabic text."""
    if not text:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    bidi_text = get_display(reshaped_text)
    return bidi_text

def generate_report(analysis: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    
    has_font = download_font_if_needed()
    if has_font:
        pdfmetrics.registerFont(TTFont('Amiri', FONT_PATH))
        font_name = 'Amiri'
    else:
        font_name = 'Helvetica'
        
    rtl_style = ParagraphStyle(
        'ArabicRight',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        alignment=TA_RIGHT,
        leading=16,
        wordWrap='RTL'
    )
    
    title_style = ParagraphStyle(
        'ArabicTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        alignment=TA_RIGHT,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'ArabicHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        alignment=TA_RIGHT,
        spaceBefore=15,
        spaceAfter=10
    )

    elements = []
    
    # Date and Title
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    elements.append(Paragraph(fix_arabic(f"تقرير تحليل العقد - {date_str}"), title_style))
    elements.append(Spacer(1, 12))
    
    # Handle error case
    if "error" in analysis:
        elements.append(Paragraph(fix_arabic("حدث خطأ أثناء التحليل:"), heading_style))
        elements.append(Paragraph(fix_arabic(analysis["error"]), rtl_style))
        doc.build(elements)
        return buffer.getvalue()

    # Summary
    elements.append(Paragraph(fix_arabic("الملخص"), heading_style))
    summary = analysis.get("summary", "لا يوجد ملخص.")
    elements.append(Paragraph(fix_arabic(summary), rtl_style))
    
    # Parties
    elements.append(Paragraph(fix_arabic("أطراف العقد"), heading_style))
    parties = analysis.get("parties", [])
    if parties:
        for party in parties:
            elements.append(Paragraph(fix_arabic(f"• {party}"), rtl_style))
    else:
        elements.append(Paragraph(fix_arabic("لم يتم العثور على أطراف للعقد."), rtl_style))
        
    # Sensitive Clauses
    elements.append(Paragraph(fix_arabic("البنود الحساسة"), heading_style))
    clauses = analysis.get("sensitive_clauses", [])
    
    if clauses:
        for clause in clauses:
            ctype = clause.get("type", "")
            ctext = clause.get("text", "")
            cloc = clause.get("location", "")
            
            # Reversing columns for RTL display in ReportLab Table
            rtl_data = [
                [Paragraph(fix_arabic(ctype), rtl_style), Paragraph(fix_arabic("النوع:"), rtl_style)],
                [Paragraph(fix_arabic(ctext), rtl_style), Paragraph(fix_arabic("النص:"), rtl_style)],
                [Paragraph(fix_arabic(cloc), rtl_style), Paragraph(fix_arabic("الموقع:"), rtl_style)]
            ]
            
            t = Table(rtl_data, colWidths=[400, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 10))
    else:
        elements.append(Paragraph(fix_arabic("لم يتم العثور على بنود حساسة."), rtl_style))
        
    doc.build(elements)
    
    return buffer.getvalue()
