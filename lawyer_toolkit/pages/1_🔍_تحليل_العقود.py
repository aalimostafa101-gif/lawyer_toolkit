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

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.warning("⚠️ يرجى إعداد مفتاح API (GEMINI_API_KEY) في ملف .env قبل الاستخدام.")

tab1, tab2 = st.tabs(["📄 رفع ملف", "📝 لصق نص"])

contract_text = ""
file_name = "contract_report.pdf"

with tab1:
    uploaded_file = st.file_uploader("قم برفع ملف العقد (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        try:
            contract_text = extract_text(uploaded_file)
            file_name = f"report_{uploaded_file.name}.pdf"
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

with tab2:
    pasted_text = st.text_area("أو قم بلصق نص العقد هنا:", height=200, placeholder="أدخل نص العقد هنا...")
    if pasted_text:
        contract_text = pasted_text
        file_name = "report_pasted_text.pdf"

disabled_analyze = not contract_text

if st.button("⚡ حلّل العقد", disabled=disabled_analyze):
    if not api_key:
        st.error("مفتاح GEMINI_API_KEY مفقود، لا يمكن إجراء التحليل. يرجى إضافته في ملف .env")
    else:
        with st.spinner("جاري تحليل العقد... يرجى الانتظار ⏳"):
            result = analyze_contract(contract_text)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state['analysis_result'] = result

if 'analysis_result' in st.session_state:
    result = st.session_state['analysis_result']
    
    st.subheader("📋 الملخص")
    st.info(result.get("summary", "لا يوجد ملخص."))
    
    st.subheader("👥 أطراف العقد")
    parties = result.get("parties", [])
    if parties:
        for party in parties:
            st.markdown(f"- {party}")
    else:
        st.markdown("لم يتم العثور على أطراف.")
        
    st.subheader("⚠️ البنود الحساسة")
    clauses = result.get("sensitive_clauses", [])
    if clauses:
        for clause in clauses:
            clause_type = clause.get("type", "أخرى")
            text = clause.get("text", "")
            location = clause.get("location", "")
            
            color = "#808080"
            if "غرامة" in clause_type:
                color = "#ff4b4b"
            elif "فسخ" in clause_type:
                color = "#ffa500"
            elif "التزام" in clause_type or "مالي" in clause_type:
                color = "#2196f3"
                
            card_html = f"""
            <div style="border-right: 4px solid {color}; padding: 10px; margin-bottom: 10px; background-color: #f8f9fa; border-radius: 5px;" dir="rtl">
                <span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; margin-bottom: 5px; display: inline-block;">{clause_type}</span>
                <p style="margin-top: 10px; color: black;">{text}</p>
                <small style="color: #666;">الموقع: {location}</small>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.markdown("لم يتم العثور على بنود حساسة.")
        
    # PDF Download
    try:
        pdf_bytes = generate_report(result)
        st.download_button(
            label="📥 تحميل تقرير PDF",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"خطأ في إنشاء التقرير: {e}")
