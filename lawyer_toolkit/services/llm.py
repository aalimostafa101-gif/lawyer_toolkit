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

    # جلب النماذج المدعومة فعلياً في حسابك من Google
    available_models = []
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as e:
        return {"error": f"فشل التحقق من مفتاح API أو جلب النماذج: {str(e)}"}

    if not available_models:
        return {"error": "لم يتم العثور على أي نموذج يدعم generateContent في هذا الحساب."}

    # تفضيل النماذج الأسرع (Flash) أولاً
    flash_models = [m for m in available_models if "flash" in m.lower()]
    other_models = [m for m in available_models if "flash" not in m.lower()]
    models_to_try = flash_models + other_models

    last_error = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "response_mime_type": "application/json",
                }
            )

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # 1. فك JSON مباشر
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass

            # 2. تنظيف Markdown code blocks
            cleaned = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
            cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE).strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

            # 3. استخراج JSON عبر Regex
            match = re.search(r"(\{[\s\S]*\})", response_text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

            last_error = f"{model_name}: استجابة غير صالحة"

        except Exception as e:
            last_error = f"{model_name} - {str(e)}"
            continue

    return {"error": f"تعذر إكمال التحليل ({last_error})."}