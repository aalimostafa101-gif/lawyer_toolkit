import json
import os
import re
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """أنت مساعد قانوني محايد متخصص في تحليل العقود العربية.
مهمتك فقط استخراج المعلومات من العقد دون إبداء أي رأي أو حكم قانوني.
لا تقدم نصائح قانونية. فقط استخرج وصنّف المعلومات.
يجب أن يكون الرد بصيغة JSON صحيحة فقط بدون أي نصوص تمهيدية أو ختامية."""

USER_PROMPT_TEMPLATE = """حلّل العقد التالي واستخرج منه بدقة:
1. ملخص قصير (3-5 جمل)
2. أطراف العقد
3. البنود الحساسة (شروط جزائية، غرامات، شروط فسخ، التزامات مالية)

العقد:
{contract_text}"""

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
        return {"error": "مفتاح API غير موجود. يرجى إضافة GEMINI_API_KEY في إعدادات Secrets."}

    genai.configure(api_key=api_key)

    contract_snippet = text[:25000] if len(text) > 25000 else text
    prompt = f"{SYSTEM_PROMPT}\n\n{USER_PROMPT_TEMPLATE.format(contract_text=contract_snippet)}"

    candidate_models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-pro"]
    last_error = ""

    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.1,
                    "response_mime_type": "application/json",
                }
            )

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # محاولة فك JSON مباشرة
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass

            # تنظيف علامات الماركداون
            cleaned = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
            cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE).strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

            # البحث عن أقواس JSON
            match = re.search(r"(\{[\s\S]*\})", response_text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

            last_error = f"{model_name}: لم يتم استخراج JSON صالح"

        except Exception as e:
            last_error = f"{model_name} - {str(e)}"
            continue

    return {"error": f"تعذر إكمال التحليل ({last_error})."}