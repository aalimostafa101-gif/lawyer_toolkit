import streamlit as st
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from utils.styles import apply_rtl_styles
from services.extractor import extract_text
from services.llm import analyze_contract
from services.pdf_report import generate_report

st.set_page_config(page_title="تحليل العقود", page_icon="🔍", layout="wide")
apply_rtl_styles()

st.title("🔍 تحليل العقود")

# التحقق من وجود مفتاح API من البيئة أو من Streamlit Secrets
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass

if not api_key:
    st.warning("⚠️ يرجى ضبط مفتاح GEMINI_API_KEY في ملف .env أو في Secrets على Streamlit Cloud.")

# تهيئة المتغيرات في session_state لتفادي ضياع النص عند الضغط على الأزرار
if 'contract_text' not in st.session_state:
    st.session_state['contract_text'] = ""
if 'file_name' not in st.session_state:
    st.session_state['file_name'] = "contract_report.pdf"

tab1, tab2 = st.tabs(["📄 رفع ملف", "📝 لصق نص"])

with tab1:
    uploaded_file = st.file_uploader("قم برفع ملف العقد (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        try:
            extracted = extract_text(uploaded_file)
            if extracted and extracted.strip():
                st.session_state['contract_text'] = extracted.strip()
                st.session_state['file_name'] = f"report_{uploaded_file.name}.pdf"
                st.success(f"تمت قراءة الملف بنجاح ({len(st.session_state['contract_text'])} حرف).")
            else:
                st.warning("تعذر استخراج نص من هذا الملف أو أن الملف فارغ/عبارة عن صور.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

with tab2:
    pasted_text = st.text_area("أو قم بلصق نص العقد هنا:", height=200, placeholder="أدخل نص العقد هنا...")
    if pasted_text and pasted_text.strip():
        st.session_state['contract_text'] = pasted_text.strip()
        st.session_state['file_name'] = "report_pasted_text.pdf"

current_text = st.session_state.get('contract_text', "").strip()
disabled_analyze = len(current_text) == 0

# إظهار معاينة مصغرة للنص الجاري تحليله
if current_text:
    with st.expander("👁️ عرض نص العقد المستخرج للتحليل"):
        st.write(current_text[:1000] + ("..." if len(current_text) > 1000 else ""))

if st.button("⚡ حلّل العقد", disabled=disabled_analyze):
    if not api_key:
        st.error("مفتاح GEMINI_API_KEY مفقود، يرجى إضافته في إعدادات Secrets.")
    else:
        with st.spinner("جاري تحليل العقد بواسطة الذكاء الاصطناعي... يرجى الانتظار ⏳"):
            result = analyze_contract(current_text)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state['analysis_result'] = result

# عرض النتائج
if 'analysis_result' in st.session_state:
    result = st.session_state['analysis_result']
    
    # 1. الملخص
    summary = result.get("summary") or result.get("ملخص") or "لا يوجد ملخص متاح."
    st.subheader("📋 الملخص")
    st.info(summary)
    
    # 2. أطراف العقد
    parties = result.get("parties") or result.get("أطراف") or []
    st.subheader("👥 أطراف العقد")
    if parties and isinstance(parties, list):
        for party in parties:
            st.markdown(f"- {party}")
    else:
        st.markdown("لم يتم العثور على أطراف.")
        
    # 3. البنود الحساسة
    clauses = result.get("sensitive_clauses") or result.get("بنود_حساسة") or []
    st.subheader("⚠️ البنود الحساسة")
    if clauses and isinstance(clauses, list):
        for clause in clauses:
            if isinstance(clause, dict):
                clause_type = clause.get("type") or clause.get("النوع") or "أخرى"
                text = clause.get("text") or clause.get("النص") or ""
                location = clause.get("location") or clause.get("الموقع") or ""
            else:
                clause_type = "بند"
                text = str(clause)
                location = ""
            
            color = "#808080"
            if "غرامة" in str(clause_type) or "جزائي" in str(clause_type):
                color = "#ff4b4b"
            elif "فسخ" in str(clause_type):
                color = "#ffa500"
            elif "التزام" in str(clause_type) or "مالي" in str(clause_type):
                color = "#2196f3"
                
            card_html = f"""
            <div style="border-right: 4px solid {color}; padding: 10px; margin-bottom: 10px; background-color: #f8f9fa; border-radius: 5px;" dir="rtl">
                <span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; margin-bottom: 5px; display: inline-block;">{clause_type}</span>
                <p style="margin-top: 10px; color: black; font-size: 0.95em;">{text}</p>
                {f'<small style="color: #666;">الموقع: {location}</small>' if location else ''}
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.markdown("لم يتم العثور على بنود حساسة.")
        
    # تحميل التقرير بصيغة PDF
    try:
        pdf_bytes = generate_report(result)
        st.download_button(
            label="📥 تحميل تقرير PDF",
            data=pdf_bytes,
            file_name=st.session_state.get('file_name', 'report.pdf'),
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"خطأ في إنشاء التقرير: {e}")