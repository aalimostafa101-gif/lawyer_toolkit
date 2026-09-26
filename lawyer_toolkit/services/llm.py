import json
import os
import re
import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# قائمة النماذج الأكثر استقراراً ودعماً
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_PROMPT = """أنت مساعد قانوني محايد متخصص في تحليل العقود العربية.
مهمتك فقط استخراج المعلومات من العقد دون إبداء أي رأي أو حكم قانوني.
لا تقدم نصائح قانونية. فقط استخرج وصنّف المعلومات.
يجب أن يكون الرد بصيغة JSON صحيحة تماماً فقط بدون أي نصوص قبلها أو بعدها."""

USER_PROMPT_TEMPLATE = """حلّل العقد التالي بدقة واستخرج منه المطلوب في قالب JSON:
1. ملخص قصير ومكثف (3-5 جمل)
2. أطراف العقد
3. أهم البنود الحساسة (غرامات، شروط جزائية، شروط فسخ، التزامات مالية)

العقد:
{contract_text}"""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "parties": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "sensitive_clauses": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {"type": "STRING"},
                    "text": {"type": "STRING"},
                    "location": {"type": "STRING"}
                },
                "required": ["type", "text", "location"]
            }
        }
    },
    "required": ["summary", "parties", "sensitive_clauses"]
}

def get_api_key() -> str:
    """جلب المفتاح سواء من Secrets أو .env"""
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

    # تقليص النص قليلاً إذا كان ضخماً جداً لضمان عدم استهلاك الذاكرة وتجاوز التوكنز
    contract_snippet = text[:25000] if len(text) > 25000 else text
    prompt = USER_PROMPT_TEMPLATE.format(contract_text=contract_snippet)

    last_error = ""
    for model_name in GEMINI_MODELS:
        try:
            url = f"{GEMINI_BASE_URL}/{model_name}:generateContent?key={api_key}"
            payload = {
                "system_instruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                },
                "contents": [
                    {"parts": [{"text": prompt}]}
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 8192,
                    "responseMimeType": "application/json",
                    "responseSchema": RESPONSE_SCHEMA,
                }
            }

            response = httpx.post(
                url,
                json=payload,
                timeout=90,
            )

            if response.status_code == 503 or (response.status_code != 200 and "high demand" in response.text):
                last_error = f"{model_name} مشغول حالياً"
                continue

            if response.status_code == 429:
                last_error = "تم تجاوز حد الطلبات المسموح (Rate limit)"
                continue

            if response.status_code != 200:
                error_data = response.json().get("error", {})
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
                if response.status_code == 403:
                    return {"error": "مفتاح API غير صالح أو صلاحيات الوصول غير مفعلة."}
                last_error = f"{model_name} - {error_msg}"
                continue

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                last_error = f"{model_name} لم يرجع أي نتيجة"
                continue

            response_text = candidates[0]["content"]["parts"][0]["text"].strip()

            # 1. محاولة فك JSON المباشر
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass

            # 2. تنظيف علامات الماركداون إن وُجدت
            clean_text = re.sub(r'^```(?:json)?\s*', '', response_text, flags=re.MULTILINE)
            clean_text = re.sub(r'```\s*$', '', clean_text, flags=re.MULTILINE).strip()
            try:
                return json.loads(clean_text)
            except json.JSONDecodeError:
                pass

            # 3. استخراج أول كائن JSON كامل بين الأقواس
            match = re.search(r'(\{[\s\S]*\})', response_text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

            last_error = "تنسيق الرد لم يكن بصيغة JSON قابلة للقراءة"

        except httpx.ConnectError:
            return {"error": "فشل الاتصال بخادم Google API. يرجى مراجعة اتصال الشبكة."}
        except httpx.TimeoutException:
            last_error = f"{model_name} استغرق وقتاً أطول من المتوقع (Timeout)"
            continue
        except Exception as e:
            last_error = f"{model_name} - {str(e)}"
            continue

    return {"error": f"تعذر إكمال التحليل ({last_error})."}