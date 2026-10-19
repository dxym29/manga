# Windows Setup (Node.js) — မြန်မာလမ်းညွှန်

ဒီ project ရဲ့ အဓိက App ကို Node.js နဲ့ ပြန်ရေးထားပါတယ်။ Python install လုပ်ဖို့ မလိုပါ။

## ၁။ လိုအပ်တာတွေ
- Node.js 20 နှင့်အထက် (npm ပါပြီးသား)
- PostgreSQL
- Gemini API key

## ၂။ Database ပြင်ဆင်ပါ
pgAdmin မှာ manga_translator ဆိုတဲ့ database တစ်ခု Create လုပ်ပါ။ PostgreSQL port က 5433 ဖြစ်ရင် .env ထဲမှာ 5433 ကိုသုံးပါ။

## ၃။ .env ဖိုင်လုပ်ပါ
VS Code terminal ထဲမှာ ဒီ command ရိုက်ပါ။
`Copy-Item .env.example .env`
ပြီးရင် .env ဖိုင်ကိုဖွင့်ပြီး DATABASE_URL နဲ့ GEMINI_API_KEY ကို ဖြည့်ပါ။
ဥပမာ:
`DATABASE_URL=postgresql://postgres:YOUR_URL_ENCODED_PASSWORD@localhost:5432/manga_translator`
`GEMINI_API_KEY=your_gemini_api_key`
`GEMINI_MODEL=gemini-2.5-flash`
Password ထဲမှာ # ပါရင် %23၊ @ ပါရင် %40 လို့ URL encode လုပ်ပါ။ ကိုယ့် password ကို GitHub ပေါ် မတင်ပါနဲ့။

## ၄။ App ကို run ပါ
VS Code terminal ထဲမှာ တစ်ကြောင်းချင်းရိုက်ပါ။
`npm install`
`npm start`
ပြီးရင် browser မှာ http://localhost:3000 ကိုဖွင့်ပါ။

## ၅။ စမ်းသပ်ပါ
1. ကိုယ်ပိုင် သို့မဟုတ် ခွင့်ပြုချက်ရှိတဲ့ manga/webtoon ပုံတွေ upload လုပ်ပါ။
2. Save chapter လုပ်ပါ။
3. Page thumbnail ကိုနှိပ်ပြီး OCR လုပ်ပါ။
4. Translate chapter with Gemini ကိုနှိပ်ပါ။
5. မြန်မာစာကို စစ်ပြီးပြင်ပါ။
6. Export ZIP လုပ်ပါ။

OCR ပထမဆုံးအကြိမ်မှာ language data download လုပ်နိုင်ပါတယ်။ Export ပုံတွေကို အသုံးမပြုခင် ပြန်စစ်ပါ။
