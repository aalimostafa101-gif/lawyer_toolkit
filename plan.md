# خطة التنفيذ — Lawyer Office AI Toolkit (MVP)

> **المرجع:** `PRD_lawyer_toolkit.md` · `lawyer_pitch_summary.md`

---

## 📐 Tech Stack

| الطبقة | الاختيار | السبب |
|---|---|---|
| واجهة المستخدم | **Streamlit** | تشغيل فوري، RTL بسيط، لا حاجة لـ frontend منفصل |
| تحليل العقود | **Anthropic Claude API** (`claude-3-5-sonnet`) | عربي ممتاز، سريع، موثوق |
| استخراج PDF | `pdfplumber` | دعم كامل للعربية/RTL |
| استخراج DOCX | `python-docx` | قراءة ملفات Word |
| تقرير PDF | `reportlab` + `arabic-reshaper` + `python-bidi` | توليد PDF عربي منسق |
| قاعدة البيانات | **SQLite** (عبر `sqlite3` المدمج) | محلي، بدون إعداد |
| متغيرات البيئة | `python-dotenv` | تمرير مفتاح الـ API بأمان |

---

## 🗂️ هيكل الملفات

```
lawyer_toolkit/
│
├── main.py                  # نقطة الدخول — Streamlit app
├── requirements.txt
├── .env.example             # ANTHROPIC_API_KEY=...
├── README.md
│
├── db/
│   ├── __init__.py
│   ├── database.py          # إنشاء الجداول + CRUD operations
│   └── lawyer.db            # يُنشأ تلقائيًا عند أول تشغيل
│
├── pages/
│   ├── contract_analysis.py # صفحة تحليل العقود
│   └── case_management.py   # صفحة إدارة القضايا والعملاء
│
├── services/
│   ├── __init__.py
│   ├── extractor.py         # استخراج النص من PDF / DOCX / TXT
│   ├── llm.py               # الاتصال بـ Claude API
│   └── pdf_report.py        # توليد تقرير PDF
│
└── utils/
    ├── __init__.py
    └── styles.py            # CSS خاص بـ RTL + الألوان
```

---

## 🔢 مراحل التنفيذ

### المرحلة 0 — الإعداد (≈ 30 دقيقة)

- [ ] إنشاء مجلد `lawyer_toolkit/` بالهيكل أعلاه
- [ ] كتابة `requirements.txt`
- [ ] إعداد `.env.example` و `.gitignore`
- [ ] كتابة `README.md` (تشغيل، ngrok، Streamlit Cloud)

---

### المرحلة 1 — قاعدة البيانات `db/database.py` (≈ 45 دقيقة)

**الجداول:**

```sql
-- عملاء
CREATE TABLE clients (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    phone      TEXT,
    email      TEXT,
    notes      TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- قضايا
CREATE TABLE cases (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id    INTEGER NOT NULL REFERENCES clients(id),
    case_number  TEXT,
    case_type    TEXT,   -- مدني / جنائي / عقاري / تجاري
    status       TEXT,   -- جارية / متوقفة / مُغلقة
    last_session DATE,
    next_session DATE,
    notes        TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**الدوال المطلوبة في `database.py`:**

| الدالة | الوصف |
|---|---|
| `init_db()` | إنشاء الجداول إن لم تكن موجودة |
| `add_client(name, phone, email, notes)` | إضافة عميل |
| `get_all_clients()` | جلب كل العملاء |
| `update_client(id, ...)` | تعديل عميل |
| `delete_client(id)` | حذف عميل (+ قضاياه) |
| `add_case(client_id, ...)` | إضافة قضية |
| `get_cases(filters)` | جلب القضايا مع فلترة |
| `update_case(id, ...)` | تعديل قضية |
| `delete_case(id)` | حذف قضية |
| `get_client_case_count(client_id)` | عدد قضايا العميل |

---

### المرحلة 2 — خدمة استخراج النص `services/extractor.py` (≈ 30 دقيقة)

```python
def extract_text(uploaded_file) -> str:
    """
    يقبل UploadedFile من Streamlit.
    يرجع النص الخام بحسب نوع الملف:
      - .pdf  -> pdfplumber
      - .docx -> python-docx
      - .txt  -> decode UTF-8
    """
```

- التعامل مع ملفات ممسوحة ضوئيًا (صور): إظهار رسالة خطأ واضحة بدلاً من إرجاع نص فارغ.
- حد النص المُرسل للـ API: اقتطاع عند ~40,000 حرف مع إشعار للمستخدم.

---

### المرحلة 3 — خدمة Claude API `services/llm.py` (≈ 45 دقيقة)

**الـ Prompt الرئيسي:**

```
أنت مساعد قانوني محايد. مهمتك فقط استخراج المعلومات من العقد التالي دون إبداء أي رأي قانوني.

أرجع ردك بـ JSON فقط بهذا الشكل:
{
  "summary": "ملخص من 3-5 جمل",
  "parties": ["الطرف الأول: ...", "الطرف الثاني: ..."],
  "sensitive_clauses": [
    {
      "type": "غرامة / فسخ / التزام مالي",
      "text": "نص البند الحرفي",
      "location": "البند رقم X أو الصفحة Y"
    }
  ]
}

العقد:
{contract_text}
```

**الدوال:**

| الدالة | الوصف |
|---|---|
| `analyze_contract(text: str) -> dict` | إرسال النص، استقبال JSON، parse |
| `_build_prompt(text: str) -> str` | بناء الـ prompt |

- معالجة أخطاء API: timeout، rate limit، JSON parse error.

---

### المرحلة 4 — توليد تقرير PDF `services/pdf_report.py` (≈ 60 دقيقة)

**محتوى التقرير:**

```
[شعار / عنوان]
تقرير تحليل العقد — {تاريخ اليوم}
─────────────────────────────
الملخص: ...

الأطراف: ...

البنود الحساسة:
  - النوع: ...
  - النص: ...
  - الموقع: ...
```

- استخدام خط عربي مدمج (Amiri أو Cairo).
- الاتجاه RTL عبر `arabic-reshaper` + `python-bidi`.
- إرجاع bytes لـ `st.download_button`.

---

### المرحلة 5 — صفحة تحليل العقود `pages/contract_analysis.py` (≈ 60 دقيقة)

**تدفق الصفحة:**

```
[عنوان الصفحة]
    │
    ├─ Tab 1: "رفع ملف"   → st.file_uploader (PDF/DOCX/TXT)
    └─ Tab 2: "لصق نص"    → st.text_area
    │
    ▼
[زر "حلّل العقد"] → spinner أثناء الانتظار
    │
    ▼
[النتائج]
    ├─ st.expander "الملخص وأطراف العقد"
    ├─ st.expander "البنود الحساسة" (كل بند في card ملونة)
    └─ [زر "تحميل تقرير PDF"]
```

- رسائل خطأ واضحة بالعربية.
- حفظ نتيجة التحليل في `st.session_state` لتجنب إعادة الطلب.

---

### المرحلة 6 — صفحة إدارة القضايا `pages/case_management.py` (≈ 90 دقيقة)

**الهيكل:**

```
[Tabs]
  ├─ القضايا
  │    ├─ فلتر (نوع + حالة)
  │    ├─ جدول القضايا
  │    ├─ [إضافة قضية جديدة] → form
  │    └─ [تعديل / حذف] لكل صف
  │
  └─ العملاء
       ├─ جدول العملاء + عدد القضايا
       ├─ [إضافة عميل جديد] → form
       └─ [تعديل / حذف] لكل صف
```

**أنواع القضايا:** مدني، جنائي، عقاري، تجاري/شركات  
**حالات القضية:** جارية، متوقفة، مُغلقة

---

### المرحلة 7 — `main.py` + Styling (≈ 30 دقيقة)

```python
# main.py
import streamlit as st
from db.database import init_db

st.set_page_config(
    page_title="أدوات المكتب الذكية",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()
```

**CSS في `utils/styles.py`:**
- `direction: rtl` على كل العناصر.
- ألوان المكتب: رمادي داكن + ذهبي.
- تنسيق cards البنود الحساسة.

---

### المرحلة 8 — الاختبار والتجميع (≈ 60 دقيقة)

- [ ] اختبار رفع PDF عربي حقيقي.
- [ ] اختبار لصق نص مباشرة.
- [ ] التحقق من صحة JSON المُرجع من Claude.
- [ ] اختبار تحميل PDF وعرضه.
- [ ] إضافة / تعديل / حذف عميل وقضية.
- [ ] الفلترة بحالات مختلفة.
- [ ] تشغيل على Streamlit Community Cloud والتأكد من ANTHROPIC_API_KEY في Secrets.

---

## ⏱️ الجدول الزمني التقديري

| المرحلة | الوصف | الوقت التقديري |
|---|---|---|
| 0 | الإعداد والهيكل | 30 دق |
| 1 | قاعدة البيانات | 45 دق |
| 2 | استخراج النص | 30 دق |
| 3 | Claude API | 45 دق |
| 4 | توليد PDF | 60 دق |
| 5 | صفحة تحليل العقود | 60 دق |
| 6 | صفحة إدارة القضايا | 90 دق |
| 7 | main.py + Styling | 30 دق |
| 8 | اختبار وتجميع | 60 دق |
| **المجموع** | | **~7.5 ساعة** |

---

## 📦 requirements.txt

```
streamlit>=1.35.0
anthropic>=0.25.0
pdfplumber>=0.11.0
python-docx>=1.1.0
reportlab>=4.2.0
arabic-reshaper>=3.0.0
python-bidi>=0.4.2
python-dotenv>=1.0.0
```

---

## 🚀 تشغيل التطبيق

```bash
# 1. تثبيت المكتبات
pip install -r requirements.txt

# 2. إعداد مفتاح API
cp .env.example .env
# ثم ضع مفتاحك في .env:
# ANTHROPIC_API_KEY=sk-ant-...

# 3. تشغيل التطبيق
streamlit run main.py
```

---

## 🔐 ملاحظات أمنية

- لا ترفع ملفات عقود حقيقية على أي منصة عامة قبل مناقشة الخصوصية مع العميل.
- مفتاح الـ API في `.env` محليًا، أو في **Streamlit Secrets** عند النشر السحابي.
- أضف `*.db` و `.env` لـ `.gitignore`.

---

## ✅ تعريف "الـ MVP جاهز"

- [ ] الأداتان تعملان بدون أخطاء على جهاز واحد.
- [ ] رفع عقد PDF عربي وتلقي تقرير كامل خلال أقل من 30 ثانية.
- [ ] إضافة / تعديل / حذف عميل وقضية بسلاسة.
- [ ] تقرير PDF يُحمَّل ويُفتح بشكل صحيح.
- [ ] الواجهة بالكامل عربية RTL وواضحة بدون شرح مسبق.
- [ ] التطبيق يعمل على Streamlit Community Cloud.
