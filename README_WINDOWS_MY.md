# Windows မှာ စတင်အသုံးပြုနည်း

## 1. လိုအပ်တာတွေ
- Python 3.11
- PostgreSQL 15 သို့မဟုတ် အထက်
- Tesseract OCR for Windows (OCR လုပ်ဖို့)
- Gemini API key (AI ဘာသာပြန်ဖို့)

## 2. PostgreSQL database ပြင်ဆင်ပါ
PostgreSQL ထဲမှာ `manga_translator` ဆိုတဲ့ database တစ်ခု ဖန်တီးပါ။ pgAdmin ကနေ Create > Database နဲ့လုပ်နိုင်ပါတယ်။

## 3. Project ကို download/clone လုပ်ပါ
PowerShell ဖွင့်ပြီး-

```powershell
git clone https://github.com/dxym29/manga.git
cd manga
Copy-Item .env.example .env
notepad .env
```

`.env` ထဲက `DATABASE_URL` ကို မိမိ PostgreSQL password နဲ့ပြင်ပါ။ Password ထဲမှာ `@`, `#`, `/`, `:` စတဲ့ အက္ခရာတွေပါရင် URL encoding လုပ်ရနိုင်ပါတယ်။ Gemini key ကို `GEMINI_API_KEY` ထဲထည့်ပါ။

## 4. Python package တွေ install လုပ်ပါ
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PowerShell က script activation ကို ပိတ်ထားရင် activation မလုပ်ဘဲ ဒီလို run ပါ-

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 5. Tesseract OCR
Tesseract OCR ကို Windows မှာ install လုပ်ပါ။ Myanmar/Japanese/Korean/Chinese စတဲ့ source language တွေအတွက် လိုအပ်တဲ့ language data ကိုလည်း ထည့်သွင်းရပါမယ်။ `.env` ထဲက `TESSERACT_CMD` ကို မိမိစက်ပေါ်ရှိ `tesseract.exe` လမ်းကြောင်းနဲ့ပြင်နိုင်ပါတယ်။

## 6. App ကိုဖွင့်ပါ
```powershell
streamlit run app.py
```
Browser မှာ `http://localhost:8501` ကိုဖွင့်ပါ။

## သတိပြုရန်
- အစပိုင်းမှာ မိမိပိုင်/ခွင့်ပြုချက်ရထားတဲ့ images သို့မဟုတ် local sample images နဲ့ စမ်းသပ်ပါ။
- URL import သည် `ALLOWED_SOURCE_DOMAINS` မပြင်ထားသေးရင် ပိတ်ထားပါတယ်။ ခွင့်ပြုချက်ရှိတဲ့ exact hostnames တွေကိုသာ ထည့်ပါ။
- ဒီ version က prototype ဖြစ်ပါတယ်။ OCR ဟာ manga font နဲ့ sound effect တွေကို လွတ်သွားနိုင်ပြီး inpainting က နောက်ခံပုံကို အမြဲမပြည့်စုံစွာ ပြန်မတည်ဆောက်နိုင်ပါ။
- မြန်မာစာအတွက် font path ထည့်ပါ။ မဟုတ်ရင် default font က မြန်မာစာကို မှန်ကန်စွာမပြနိုင်ပါ။
- `.env` ကို GitHub မတင်ပါနဲ့။
