# ⚖️ أدوات المكتب الذكية — Lawyer Office AI Toolkit

نسخة أولية (MVP) لأداتين ذكيتين لمكتب محاماة:
1. **🔍 تحليل العقود** — رفع عقد (PDF/Word/نص) والحصول على ملخص فوري + رصد البنود الحساسة
2. **📊 إدارة القضايا والعملاء** — متابعة القضايا والعملاء مع فلترة وتعديل

---

## 🚀 التشغيل السريع

### المتطلبات
- Python 3.9+
- مفتاح Anthropic API

### الخطوات

```bash
# 1. انتقل لمجلد المشروع
cd lawyer_toolkit

# 2. ثبّت المكتبات
pip install -r requirements.txt

# 3. أنشئ ملف .env وضع مفتاح API
cp .env.example .env
# عدّل .env وضع مفتاحك:
# ANTHROPIC_API_KEY=sk-ant-...

# 4. شغّل التطبيق
streamlit run main.py
```

التطبيق هيفتح على `http://localhost:8501`

---

## 📱 عرض التطبيق في الاجتماع

### الطريقة 1: نفس شبكة Wi-Fi
```bash
streamlit run main.py --server.address 0.0.0.0
```
افتح الرابط `http://<your-ip>:8501` من أي جهاز على نفس الشبكة.

### الطريقة 2: رابط مؤقت عبر ngrok
```bash
pip install pyngrok
ngrok http 8501
```
استخدم الرابط العام اللي ngrok يوفّره.

### الطريقة 3: Streamlit Community Cloud (الأفضل)
1. ارفع المشروع على GitHub
2. اربطه بـ [share.streamlit.io](https://share.streamlit.io)
3. أضف `ANTHROPIC_API_KEY` في **Secrets** من الإعدادات

---

## 🗂️ هيكل المشروع

```
lawyer_toolkit/
├── main.py                     # الصفحة الرئيسية
├── requirements.txt
├── .env.example
├── .gitignore
├── db/
│   ├── database.py             # قاعدة البيانات SQLite
│   └── lawyer.db               # يُنشأ تلقائيًا
├── pages/
│   ├── 1_🔍_تحليل_العقود.py    # صفحة تحليل العقود
│   └── 2_📊_إدارة_القضايا.py   # صفحة إدارة القضايا
├── services/
│   ├── extractor.py            # استخراج النص من الملفات
│   ├── llm.py                  # الاتصال بـ Claude API
│   └── pdf_report.py           # توليد تقارير PDF
└── utils/
    └── styles.py               # تنسيقات RTL والألوان
```

---

## 🔐 ملاحظات أمنية

- **لا ترفع عقود حقيقية** على أي منصة عامة قبل مناقشة الخصوصية مع العميل.
- مفتاح API يُحفظ في `.env` محليًا (مُضاف لـ `.gitignore`).
- قاعدة البيانات محلية بالكامل (SQLite).

---

## 📝 نسخة تجريبية — MVP
هذا المنتج نسخة أولى للعرض. الميزات القادمة:
- نظام مستخدمين متعدد وصلاحيات
- تكامل البريد الإلكتروني
- متابعة مالية (فواتير ومستحقات)
- قاعدة بيانات سحابية مشفّرة
