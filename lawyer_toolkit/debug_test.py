import os, httpx, json
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GEMINI_API_KEY')

test_contract = "البند الخامس السرية والملكية الفكرية. تؤول كافة حقوق الملكية الفكرية والاكواد المصدرية الناتجة عن المشروع للطرف الاول فور سداد كامل المستحقات المالية. البند السادس فسخ العقد والشروط الجزائية. يحق للطرف الاول انهاء هذا العقد في اي وقت دون ابداء اسباب. بينما يلتزم الطرف الثاني بدفع تعويض مقداره 20000 جنيه في حال تعذر عليه اكمال المشروع."

prompt = 'حلل هذا العقد وارجع JSON فقط بدون اي نص اخر بالشكل: {"summary": "...", "parties": ["..."], "sensitive_clauses": [{"type": "...", "text": "...", "location": "..."}]}\n\nالعقد:\n' + test_contract

for model in ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.5-flash', 'gemini-2.5-flash']:
    try:
        r = httpx.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}',
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 2048}
            },
            verify=False, timeout=30
        )
        if r.status_code == 200:
            txt = r.json()['candidates'][0]['content']['parts'][0]['text']
            with open('debug_response.txt', 'w', encoding='utf-8') as f:
                f.write(f'MODEL: {model}\n\n{txt}')
            print(f'Model: {model} OK, length: {len(txt)}')
            break
        else:
            print(f'Model: {model} - Status: {r.status_code}')
    except Exception as e:
        print(f'Model: {model} - Error: {e}')
