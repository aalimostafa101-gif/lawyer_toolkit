import json
import os
import re
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_PROMPT = """أنت مساعد قانوني محايد متخصص في تحليل العقود العربية.
مهمتك فقط استخراج المعلومات من العقد دون إبداء أي رأي أو حكم قانوني.
لا تقدم نصائح قانونية. فقط استخرج وصنّف المعلومات."""

USER_PROMPT_TEMPLATE = """حلّل العقد التالي واستخرج منه:
1. ملخص قصير (3-5 جمل)
2. أطراف العقد
3. البنود الحساسة (غرامات، شروط فسخ، التزامات مالية)

أرجع الناتج بصيغة JSON فقط بالشكل التالي:
{{
  "summary": "ملخص العقد",
  "parties": ["الطرف الأول: ...", "الطرف الثاني: ..."],
  "sensitive_clauses": [
    {{
      "type": "غرامة أو شرط فسخ أو التزام مالي",
      "text": "نص البند الحرفي من العقد",
      "location": "البند رقم X أو الفقرة Y"
    }}
  ]
}}

لا تكتب أي شيء قبل أو بعد الـ JSON.

العقد:
{contract_text}"""


def analyze_contract(text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "مفتاح API غير موجود. يرجى إضافة GEMINI_API_KEY في ملف .env"}

    prompt = USER_PROMPT_TEMPLATE.format(contract_text=text)

    last_error = ""
    for model_name in GEMINI_MODELS:
        try:
            url = f"{GEMINI_BASE_URL}/{model_name}:generateContent?key={api_key}"
            response = httpx.post(
                url,
                json={
                    "system_instruction": {
                        "parts": [{"text": SYSTEM_PROMPT}]
                    },
                    "contents": [
                        {"parts": [{"text": prompt}]}
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 2048,
                    }
                },
                verify=False,
                timeout=60,
            )

            if response.status_code == 503 or (response.status_code != 200 and "high demand" in response.text):
                last_error = f"{model_name} مشغول حالياً"
                continue  # Try next model

            if response.status_code == 429:
                last_error = "تم تجاوز الحد المسموح"
                continue

            if response.status_code != 200:
                error_data = response.json().get("error", {})
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
                if response.status_code == 403:
                    return {"error": "مفتاح API غير صالح أو الخدمة غير مفعّلة."}
                return {"error": f"خطأ في API: {error_msg}"}

            data = response.json()
            response_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

            # Try direct JSON parse first (cleanest response)
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass

            # Try extracting from markdown code block
            match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
            if match:
                return json.loads(match.group(1))

            # Try finding the outermost JSON object
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            if first_brace != -1 and last_brace != -1:
                return json.loads(response_text[first_brace:last_brace + 1])

            return {"error": "الموديل لم يرجع JSON صالح. يرجى المحاولة مرة أخرى."}

        except httpx.ConnectError:
            return {"error": "فشل الاتصال بخادم API. يرجى التحقق من اتصال الإنترنت."}
        except httpx.TimeoutException:
            last_error = f"{model_name} - انتهت المهلة"
            continue
        except json.JSONDecodeError:
            return {"error": "فشل في تحليل الرد كـ JSON. يرجى المحاولة مرة أخرى."}
        except Exception as e:
            return {"error": f"حدث خطأ غير متوقع: {str(e)}"}

    return {"error": f"جميع الموديلات مشغولة حالياً ({last_error}). حاول مرة أخرى بعد دقيقة."}
