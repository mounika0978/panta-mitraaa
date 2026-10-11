# Local Farming Decision Assistant (academic prototype)

AI-powered local farming decision assistant for rain-fed farmers in Andhra Pradesh.
Telugu-first, light enough for 2G/3G phones (CSS + JS is about 10 KB; no CDNs, frameworks or font downloads).
**Decisions come from editable JSON rule files. There is no machine-learning model.** The "AI assistant" chat box and the voice assistant only retrieve and explain those verified rules.

## Setup, run, test

Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit ADMIN_PASSWORD
python -m app.seed
uvicorn app.main:app --reload
pytest
```
Windows (PowerShell):
```powershell
py -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # then edit ADMIN_PASSWORD
python -m app.seed
uvicorn app.main:app --reload
pytest
```
Open http://localhost:8000. Health check: /health. Admin: /admin/callbacks (user `admin`, password = `ADMIN_PASSWORD`). If `ADMIN_PASSWORD` is empty the admin page stays locked.

## Features
1. Farmer profile (several profiles per mobile number; stage calculated from days after sowing).
2. Dry-spell advisory from `data/rules/dry_spell_rules.json` + `advice_rules.json`; every card shows risk (icon + text), reasons, rule IDs, actions, data source/date, rules version and the disclaimer. A scenario switcher changes the simulated weather live.
3. Telugu default, English toggle (all text in `data/i18n/*.json`; toggling never reloads the page, so form data is kept).
4. Expert callback request + password-protected admin list.
5. Crop photo upload (type checked with Pillow, EXIF/GPS removed, random filenames, preliminary quality review only).
6. **AI assistant chat box** (button at bottom right of every page).
7. **Voice assistant**: tap the microphone, speak in Telugu or English, hear the reply (tick "Voice replies" to hear typed answers too).

## How the chat assistant works (for the viva)
`app/assistant.py` decides in this order, so each answer traces to a named rule:
1. Dose, quantity or product questions are refused (`SAFETY-NO-DOSE`) and the farmer is pointed to an expert.
2. If a farm profile is open and the question is about weather/risk/advice, it explains that profile's advisory (rule IDs such as `DS-H1`, `ADV-ANY-HIGH`).
3. Otherwise the best-matching entry in `data/rules/chat_faq.json` answers (`FAQ-...`).
4. Otherwise it says it has no verified answer and offers an expert callback.
Every reply shows its source line. To teach it something new, add an entry to `chat_faq.json`. No code change is needed.

## Voice assistant: what to know
- It uses the browser's built-in Web Speech API (no library, no CDN, no key).
- **Voice input** works in Chrome-like browsers only, on **HTTPS or localhost**, with microphone permission. Chrome sends the audio to Google's servers, so it needs internet.
- **Voice output** uses the phone's text-to-speech. Many phones need the Telugu voice installed (Settings > Language > Text-to-speech). The page shows a hint if none is found.
- If voice is unavailable the mic button hides and typing still works.
- Demo tip: use the laptop with `localhost`. A phone opening `http://192.168.x.x:8000` will NOT allow the microphone (not a secure context).

## Assumptions
- Districts: the 26 districts of Andhra Pradesh after the 2022 reorganisation (`data/seed/districts.json`). Verify against the latest notification; the list may change.
- "Millet" means **pearl millet (bajra, Telugu: sajja)**. "Red gram" means pigeon pea (kandi).
- Crop stage ranges (days after sowing) in `crop_stages.json` and all dry-spell thresholds are **illustrative PLACEHOLDERS**: validate against ANGRAU/KVK guidance before real use.
- Weather is simulated (`weather_scenarios.json`). `OpenWeatherProvider` is only a stub and refuses to run in demo mode or without `WEATHER_API_KEY`.
- Sowing date must be within the last year or up to 30 days ahead.
- Demo mobile numbers and names in the seed are invented.

## Limitations
- **No login or OTP.** A mobile number is only an identifier, so anyone who knows a number can look up its profiles. Do not store real farmers' data in this prototype.
- Admin uses HTTP Basic auth without CSRF protection (acceptable for a demo only).
- No rate limiting, no HTTPS inside the app (use a reverse proxy or tunnel if needed).
- Photo review checks only resolution, brightness and sharpness. It never names a disease (`classify_disease` returns `None`).
- The chat assistant is keyword-based and can miss questions phrased in unexpected ways. It falls back to an expert referral.

## Machine-drafted Telugu (needs review by a Telugu speaker)
All Telugu text was machine-drafted. Run `python -m app.review_list` to print every Telugu string with its file and key (131 strings). They live in `data/i18n/te.json`, `data/rules/*.json` and `data/seed/weather_scenarios.json`.

## 5-step demo script
1. **Home.** "Farmers enter their crop and sowing date in Telugu; consent comes first." Toggle English to show nothing is lost. Open Ramesh's profile via the mobile number `9876543210` (two crops) and note the masked number.
2. **Advisory.** Open the groundnut profile. Point at the stage (calculated from days after sowing) and the risk card (icon + word, not colour alone).
3. **Live scenario switch.** Change to "Severe dry spell". Risk turns High. Open "Why this advice?" and read the rule IDs `DS-H1` and `ADV-GN-FLW-HIGH`. "Every advisory traces to a named rule in an editable JSON file."
4. **Assistant + voice.** Open the chat, ask "what is my risk?" (or tap the mic and ask in Telugu). Then ask "how much urea per acre?" and show the safe refusal.
5. **Safety flows.** Upload a photo (preliminary review only, EXIF removed), submit an expert callback, then show `/admin/callbacks` (password) and mark one resolved.
