import json
import os
import re
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """أنت خبير قانوني ومساعد محايد في تدقيق وتحليل العقود العربية.
استخرج من العقد المُعطى البيانات المطلوبة بدقة تامة وبصيغة JSON حصراً.
يجب أن يحتوي الرد على هذه المفاتيح بالضبط:
- "summary": نص من عدة جمل يلخص جوهر العقد والالتزامات الرئيسية.
- "parties": قائمة بأسماء الأطراف المذكورة في العقد (مصفوفة نصوص).
- "sensitive_clauses": قائمة بالبنود الحساسة (شروط جزائية، غرامات، صلاحيات فسخ، مبالغ وتأمينات). كل عنصر كائن يحتوي على:
    * "type": نوع البند (غرامة / شرط جزائي / فسخ / التزام مالي / أخرى)
    * "text": النص الحرفي للبند أو ملخصه
    * "location": رقم البند أو مكانه في العقد
"""

def get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
    return api_key

def analyze_contract(text: str) -> dict:
    api_key = get_api_key()
    if not api_key:
        return {"error": "مفتاح API غير متوفر في النظام."}

    if not text or len(text.strip()) < 10:
        return {"error": "النص المدخل فارغ أو قصير جداً للتحليل."}

    genai.configure(api_key=api_key)

    prompt = f"{SYSTEM_PROMPT}\n\nنص العقد للتحليل:\n\"\"\"\n{text}\n\"\"\"\n\nأرجع JSON فقط:"

    # النماذج الأكثر انتشاراً للتوليد
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.5-flash"]
    
    last_error = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name=model_name)
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                continue

            raw = response.text.strip()
            
            # تنظيف علامات الماركداون
            cleaned = re.sub(r"^```(?:json)?", "", raw, flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

            data = None
            try:
                data = json.loads(cleaned)
            except Exception:
                # استخراج أول كتلة JSON بواسطة regex
                match = re.search(r"(\{[\s\S]*\})", raw)
                if match:
                    data = json.loads(match.group(1))

            if isinstance(data, dict):
                # التأكد من المفاتيح أو جلب بدائلها
                summary = data.get("summary") or data.get("ملخص") or data.get("contract_summary") or ""
                parties = data.get("parties") or data.get("أطراف") or data.get("parties_involved") or []
                clauses = data.get("sensitive_clauses") or data.get("بنود_حساسة") or data.get("clauses") or []

                return {
                    "summary": summary if summary else "تم تحليل العقد ولكن لم يُذكر ملخص صريح.",
                    "parties": parties,
                    "sensitive_clauses": clauses
                }

        except Exception as e:
            last_error = f"{model_name}: {str(e)}"
            continue

    return {"error": f"تعذر استخراج البيانات ({last_error})"}