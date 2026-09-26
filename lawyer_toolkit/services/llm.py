"""
services/llm.py
-----------------
تحليل عقود عربية عبر Gemini API (Google).

نسخة تشخيصية: بتجرب كل موديل في القائمة، وبدل ما تورينا خطأ آخر موديل بس
(اللي بيبقى مضلل)، بتجمع خطأ كل موديل على حدة وتوريهم كلهم عشان نعرف
بالظبط ليه gemini-3.8-flash نفسه بيفشل.
"""

import json
import os

from google import genai
from google.genai import types

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-2.5-flash"]

SYSTEM_PROMPT = """\
أنت مساعد يقرأ عقود قانونية مكتوبة بالعربية ومهمتك تلخيص العقد ولفت نظر
المستخدم إلى البنود التي تحتوي على التزامات أو أرقام أو شروط واضحة، فقط.

قواعد صارمة يجب الالتزام بها:
- لا تُصدر أي حكم قانوني على عدالة أو صحة أي بند.
- لا تقارن العقد بأي "معيار قانوني" افتراضي.
- ركّز فقط على البنود التي تحتوي على واحد أو أكثر من التالي بشكل صريح
  في نص العقد: غرامات مالية أو تأخير، شروط فسخ أو إنهاء العقد،
  التزامات مالية (مبالغ، دفعات، ضمانات)، مدد زمنية حرجة (مواعيد نهائية).
- إذا لم يوجد بند من هذا النوع، أعد قائمة فارغة بدل اختلاق بنود.
- أعد الإجابة بصيغة JSON فقط بدون أي نص إضافي قبله أو بعده، وبنفس أسماء
  الحقول التالية حرفيًا:

{
  "summary": "ملخص قصير للعقد في 3-5 جمل بالعربية الفصحى البسيطة",
  "parties": ["الطرف الأول (كما ورد في العقد)", "الطرف الثاني (كما ورد في العقد)"],
  "sensitive_clauses": [
    {
      "type": "غرامة تأخير | شرط فسخ | التزام مالي | مدة حرجة | أخرى",
      "text": "نص البند أو تلخيص دقيق له",
      "location": "رقم البند/المادة كما ورد في العقد، أو وصف مختصر لموضعه"
    }
  ]
}
"""


def _clean_json_text(raw_text: str) -> str:
    """يشيل أي ```json``` أو ``` حوالين رد الموديل قبل الـ parsing."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


def analyze_contract(contract_text: str, api_key: str) -> dict:
    """
    بيرجع dict فيه: summary, parties, sensitive_clauses
    بيجرب PRIMARY_MODEL الأول، ولو فشل يجرب الموديلات الاحتياطية بالترتيب.
    لو الكل فشل، بيرفع خطأ واحد فيه تفاصيل فشل كل موديل على حدة (مش آخر واحد بس).
    """
    if not api_key:
        raise RuntimeError("لازم تدخل مفتاح Gemini API (GOOGLE_API_KEY).")

    trimmed_text = contract_text[:40000]
    client = genai.Client(api_key=api_key)

    errors_per_model = []  # هنجمع هنا خطأ كل موديل بالتفصيل

    for model_name in [PRIMARY_MODEL, *FALLBACK_MODELS]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=trimmed_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                ),
            )
            cleaned = _clean_json_text(response.text)
            data = json.loads(cleaned)

            data.setdefault("summary", "")
            data.setdefault("parties", [])
            data.setdefault("sensitive_clauses", [])
            data["_model_used"] = model_name
            return data

        except Exception as e:  # noqa: BLE001
            # بنسجل نوع الخطأ ورسالته كاملة لكل موديل، مش بس آخر واحد
            errors_per_model.append(f"[{model_name}] {type(e).__name__}: {e}")
            continue

    details = "\n".join(errors_per_model)
    raise RuntimeError(
        "فشل التحليل بكل الموديلات المتاحة. تفاصيل كل موديل على حدة:\n"
        f"{details}"
    )
